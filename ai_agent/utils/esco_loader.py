"""
utils/esco_loader.py
────────────────────
ESCOLoader: loads the three ESCO v1.1.1 CSV files and exposes:

  - build_index()               encode occupations → NPY + JSON cache
  - find_closest_occupation()   semantic role lookup
  - get_role_skill_profile()    essential / optional skills for a URI
  - get_skill_definition()      ESCO skill description by label
  - get_related_skills()        co-occurring skills across occupations

All public methods are safe to call when ESCO data is absent (graceful
fallback — is_loaded=False, every method returns an empty result).

The sentence-transformers model is NEVER loaded here; the caller passes
it in as a parameter so the existing get_model() singleton is reused.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional, cast

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _col(df: pd.DataFrame, candidates: list[str]) -> str:
    """Return the first column name from *candidates* that exists in *df*."""
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(
        f"None of {candidates} found in DataFrame columns: {list(df.columns)}"
    )


# ── ESCOLoader ────────────────────────────────────────────────────────────────

class ESCOLoader:
    """
    Loads and indexes ESCO v1.1.1 taxonomy data.

    Parameters
    ----------
    data_dir : str
        Path to the directory containing occupations_en.csv, skills_en.csv,
        and occupationSkillRelations_en.csv (or occupationSkillRelations.csv).

    Attributes
    ----------
    is_loaded : bool
        True when all three CSV files were found and loaded successfully.
    occupations : pd.DataFrame   (empty when not loaded)
    skills      : pd.DataFrame   (empty when not loaded)
    relations   : pd.DataFrame   (empty when not loaded)
    """

    def __init__(self, data_dir: str) -> None:
        self.data_dir: Path = Path(data_dir).resolve()
        self.is_loaded: bool = False

        # Public DataFrames
        self.occupations: pd.DataFrame = pd.DataFrame()
        self.skills: pd.DataFrame = pd.DataFrame()
        self.relations: pd.DataFrame = pd.DataFrame()

        # Index state (populated by build_index)
        self._occ_embeddings: Optional[np.ndarray] = None   # shape (N, D)
        self._occ_uris: list[str] = []                       # parallel to embeddings
        self._occ_titles: list[str] = []
        self._skills_index: dict[str, dict] = {}             # uri → {label, description, skill_type}
        self._label_to_uri: dict[str, str] = {}              # lowercase label → uri
        self._cooccurrence: dict[str, dict[str, int]] = {}   # skill_uri → {skill_uri: count}

        self._load()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load the three ESCO CSV files.  Sets is_loaded=True on success."""
        occ_path = self.data_dir / "occupations_en.csv"
        sk_path  = self.data_dir / "skills_en.csv"
        # Accept both ESCO naming conventions
        rel_path = (
            self.data_dir / "occupationSkillRelations.csv"
            if (self.data_dir / "occupationSkillRelations.csv").exists()
            else self.data_dir / "occupationSkillRelations_en.csv"
        )

        missing = [p for p in [occ_path, sk_path, rel_path] if not p.exists()]
        if missing:
            logger.warning(
                "ESCOLoader: %d file(s) not found — running in fallback mode.\n"
                "  Missing: %s",
                len(missing),
                ", ".join(str(p) for p in missing),
            )
            return

        try:
            logger.info("ESCOLoader: loading CSV files from %s …", self.data_dir)
            self.occupations = pd.read_csv(occ_path, low_memory=False)
            self.skills      = pd.read_csv(sk_path,  low_memory=False)
            self.relations   = pd.read_csv(rel_path,  low_memory=False)
            logger.info(
                "ESCOLoader: loaded %d occupations, %d skills, %d relations",
                len(self.occupations), len(self.skills), len(self.relations),
            )
            self.is_loaded = True
        except Exception as exc:
            logger.warning("ESCOLoader: failed to load CSV files — %s", exc)

    # ------------------------------------------------------------------
    # Index building
    # ------------------------------------------------------------------

    def build_index(self, model: Any, cache_dir: str) -> None:
        """
        Encode all occupation labels and build lookup indexes.

        If cache files exist in *cache_dir*, they are loaded instead of
        re-encoding (avoids ~30 s startup cost on subsequent runs).

        Parameters
        ----------
        model     : SentenceTransformer instance (passed in, NOT loaded here)
        cache_dir : directory where .npy / .json cache files are stored
        """
        if not self.is_loaded:
            logger.warning("ESCOLoader.build_index: data not loaded — skipping.")
            return

        cache = Path(cache_dir)
        cache.mkdir(parents=True, exist_ok=True)

        emb_path  = cache / "occupation_embeddings.npy"
        occ_path  = cache / "occupation_index.json"
        sk_path   = cache / "skills_index.json"

        # ── Skill index (always rebuilt from CSV — fast) ──────────────
        self._build_skills_index(sk_path)

        # ── Occupation embeddings ─────────────────────────────────────
        if emb_path.exists() and occ_path.exists():
            logger.info("ESCOLoader: loading occupation embeddings from cache …")
            self._occ_embeddings = np.load(str(emb_path))
            with open(occ_path, "r", encoding="utf-8") as f:
                occ_index = json.load(f)
            self._occ_uris   = occ_index["uris"]
            self._occ_titles = occ_index["titles"]
            logger.info(
                "ESCOLoader: loaded %d occupation embeddings from cache.",
                len(self._occ_uris),
            )
        else:
            self._encode_occupations(model, emb_path, occ_path)

        # ── Co-occurrence index ────────────────────────────────────────
        self._build_cooccurrence_index()

        logger.info("ESCOLoader: index ready.")

    def _build_skills_index(self, sk_path: Path) -> None:
        """Build {uri: {label, description, skill_type}} index and save to disk."""
        sk = self.skills.copy()
        uri_col  = _col(sk, ["conceptUri", "uri"])
        lbl_col  = _col(sk, ["preferredLabel", "label"])
        desc_col = _col(sk, ["description", "altLabels"]) if "description" in sk.columns else None
        type_col = _col(sk, ["skillType", "type"]) if "skillType" in sk.columns else None

        index: dict[str, dict] = {}
        label_to_uri: dict[str, str] = {}

        for _, row in sk.iterrows():
            uri   = str(row.get(uri_col, ""))
            label = str(row.get(lbl_col, "")).strip()
            if not uri or not label:
                continue

            entry: dict[str, str] = {"label": label}
            if desc_col:
                entry["description"] = str(row.get(desc_col, ""))
            if type_col:
                entry["skill_type"] = str(row.get(type_col, ""))

            index[uri] = entry
            label_to_uri[label.lower()] = uri

        self._skills_index  = index
        self._label_to_uri  = label_to_uri

        with open(sk_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False)
        logger.info("ESCOLoader: skills index saved (%d entries).", len(index))

    def _encode_occupations(
        self,
        model: Any,
        emb_path: Path,
        occ_path: Path,
    ) -> None:
        """Encode all occupation labels and save embeddings to disk."""
        lbl_col = _col(self.occupations, ["preferredLabel", "label"])
        uri_col = _col(self.occupations, ["conceptUri", "uri"])

        occ_df = self.occupations.dropna(subset=[lbl_col, uri_col]).copy()
        labels = cast(list[str], occ_df[lbl_col].astype(str).tolist())
        uris   = cast(list[str], occ_df[uri_col].astype(str).tolist())
        titles = labels  # same values, kept separate for clarity

        logger.info(
            "ESCOLoader: encoding %d occupation labels (this may take ~30 s)…",
            len(labels),
        )

        batch_size = 64
        all_embeddings: list[np.ndarray] = []
        for start in range(0, len(labels), batch_size):
            batch = labels[start : start + batch_size]
            embs  = model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
            all_embeddings.append(embs)
            if (start // batch_size + 1) % (500 // batch_size) == 0:
                logger.info(
                    "ESCOLoader: encoded %d / %d occupations …",
                    min(start + batch_size, len(labels)),
                    len(labels),
                )

        embeddings = np.vstack(all_embeddings).astype(np.float32)
        np.save(str(emb_path), embeddings)

        occ_index = {"uris": uris, "titles": titles}
        with open(occ_path, "w", encoding="utf-8") as f:
            json.dump(occ_index, f, ensure_ascii=False)

        self._occ_embeddings = embeddings
        self._occ_uris       = uris
        self._occ_titles     = titles
        logger.info(
            "ESCOLoader: saved %d occupation embeddings → %s",
            len(uris), emb_path,
        )

    def _build_cooccurrence_index(self) -> None:
        """
        Build a co-occurrence map: for each skill, which other skills
        appear in the same occupation.  Used by get_related_skills().
        """
        if self.relations.empty:
            return

        occ_col  = _col(self.relations, ["occupationUri", "occupation"])
        sk_col   = _col(self.relations, ["skillUri", "skill"])

        cooc: dict[str, dict[str, int]] = {}
        grouped = self.relations.groupby(occ_col)[sk_col].apply(list)

        for skill_list in grouped:
            for skill_a in skill_list:
                for skill_b in skill_list:
                    if skill_a == skill_b:
                        continue
                    cooc.setdefault(skill_a, {})
                    cooc[skill_a][skill_b] = cooc[skill_a].get(skill_b, 0) + 1

        self._cooccurrence = cooc
        logger.debug("ESCOLoader: co-occurrence index built.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_closest_occupation(
        self,
        role_text: str,
        model: Any,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Semantic lookup: find the closest ESCO occupation(s) to *role_text*.

        Parameters
        ----------
        role_text : free-form text (job title, JD excerpt, etc.)
        model     : SentenceTransformer instance
        top_k     : number of results to return

        Returns
        -------
        list of dicts: [{uri, title, similarity_score}]  — empty on failure.
        """
        if not self.is_loaded or self._occ_embeddings is None:
            return []

        try:
            query_emb = model.encode(role_text, convert_to_numpy=True).astype(np.float32)

            # Cosine similarity via dot product on L2-normalised vectors
            norms = np.linalg.norm(self._occ_embeddings, axis=1, keepdims=True)
            normed_embs = self._occ_embeddings / np.clip(norms, 1e-9, None)
            q_norm = query_emb / np.clip(np.linalg.norm(query_emb), 1e-9, None)

            similarities = normed_embs @ q_norm
            top_indices  = np.argsort(similarities)[::-1][:top_k]

            return [
                {
                    "uri":              self._occ_uris[i],
                    "title":            self._occ_titles[i],
                    "similarity_score": float(round(similarities[i], 4)),
                }
                for i in top_indices
            ]
        except Exception as exc:
            logger.warning("find_closest_occupation failed: %s", exc)
            return []

    def get_role_skill_profile(self, occupation_uri: str) -> dict[str, Any]:
        """
        Return the full skill profile for an occupation URI.

        Parameters
        ----------
        occupation_uri : e.g. 'http://data.europa.eu/esco/occupation/…'

        Returns
        -------
        {
          essential_skills: list[str],
          optional_skills:  list[str],
          knowledge_areas:  list[str],
          esco_occupation_title: str,
          total_skills: int,
        }
        """
        empty: dict[str, Any] = {
            "essential_skills":       [],
            "optional_skills":        [],
            "knowledge_areas":        [],
            "esco_occupation_title":  "",
            "total_skills":           0,
        }
        if not self.is_loaded or self.relations.empty:
            return empty

        try:
            occ_col  = _col(self.relations, ["occupationUri", "occupation"])
            sk_col   = _col(self.relations, ["skillUri", "skill"])
            rel_col  = _col(self.relations, ["relationType", "type"]) \
                       if "relationType" in self.relations.columns else None

            subset = self.relations[self.relations[occ_col] == occupation_uri]
            if subset.empty:
                return empty

            essential: list[str] = []
            optional:  list[str] = []
            knowledge: list[str] = []

            for _, row in subset.iterrows():
                uri   = str(row[sk_col])
                entry = self._skills_index.get(uri, {})
                label = entry.get("label", uri)
                stype = entry.get("skill_type", "")

                if "knowledge" in stype.lower():
                    knowledge.append(label)
                elif rel_col and str(row.get(rel_col, "")).lower() == "essential":
                    essential.append(label)
                elif rel_col and str(row.get(rel_col, "")).lower() == "optional":
                    optional.append(label)
                else:
                    essential.append(label)  # default to essential

            # Resolve occupation title
            title = ""
            if not self.occupations.empty:
                uri_col = _col(self.occupations, ["conceptUri", "uri"])
                lbl_col = _col(self.occupations, ["preferredLabel", "label"])
                match = self.occupations[self.occupations[uri_col] == occupation_uri]
                if not match.empty:
                    title = str(match.iloc[0][lbl_col])

            return {
                "essential_skills":       list(dict.fromkeys(essential)),
                "optional_skills":        list(dict.fromkeys(optional)),
                "knowledge_areas":        list(dict.fromkeys(knowledge)),
                "esco_occupation_title":  title,
                "total_skills":           len(essential) + len(optional) + len(knowledge),
            }

        except Exception as exc:
            logger.warning("get_role_skill_profile(%s) failed: %s", occupation_uri, exc)
            return empty

    def get_skill_definition(self, skill_label: str) -> str:
        """
        Look up an ESCO skill definition by label (case-insensitive).

        Parameters
        ----------
        skill_label : e.g. 'python (programming language)'

        Returns
        -------
        description string or '' if not found
        """
        uri = self._label_to_uri.get(skill_label.lower().strip())
        if uri:
            return self._skills_index.get(uri, {}).get("description", "")
        return ""

    def get_related_skills(self, skill_label: str, n: int = 5) -> list[str]:
        """
        Return the top-*n* skills that co-occur most often with *skill_label*
        across all ESCO occupations.

        Parameters
        ----------
        skill_label : skill label (case-insensitive)
        n           : maximum number of related skills to return

        Returns
        -------
        list of skill label strings (most related first)
        """
        uri = self._label_to_uri.get(skill_label.lower().strip())
        if not uri or uri not in self._cooccurrence:
            return []

        co_counts = self._cooccurrence[uri]
        top_uris  = sorted(co_counts, key=co_counts.get, reverse=True)[:n]  # type: ignore
        return [
            self._skills_index[u]["label"]
            for u in top_uris
            if u in self._skills_index
        ]
