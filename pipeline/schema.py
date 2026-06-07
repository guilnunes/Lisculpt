"""Lisculpt schema helpers — mirrors the field structure of sculptors.json."""

import re

MATERIAL_AAT = {
    "Bronze":      "http://vocab.getty.edu/aat/300010957",
    "Clay":        "http://vocab.getty.edu/aat/300010439",
    "Marble":      "http://vocab.getty.edu/aat/300011443",
    "Stone":       "http://vocab.getty.edu/aat/300011176",
    "Ceramics":    "http://vocab.getty.edu/aat/300010660",
    "Ceramic":     "http://vocab.getty.edu/aat/300010660",
    "Wood":        "http://vocab.getty.edu/aat/300011914",
    "Steel":       "http://vocab.getty.edu/aat/300010900",
    "Iron":        "http://vocab.getty.edu/aat/300010929",
    "Aluminum":    "http://vocab.getty.edu/aat/300010975",
    "Aluminium":   "http://vocab.getty.edu/aat/300010975",
    "Glass":       "http://vocab.getty.edu/aat/300010797",
    "Resin":       "http://vocab.getty.edu/aat/300014566",
    "Plaster":     "http://vocab.getty.edu/aat/300014922",
    "Wax":         "http://vocab.getty.edu/aat/300011929",
    "Terracotta":  "http://vocab.getty.edu/aat/300010669",
    "Fiberglass":  "http://vocab.getty.edu/aat/300010525",
    "Fibreglass":  "http://vocab.getty.edu/aat/300010525",
    "Polyester":   "http://vocab.getty.edu/aat/300014789",
}


def slugify(name: str) -> str:
    """Convert an artist name to a URL-safe slug matching existing sculptors.json IDs."""
    slug = name.lower()
    slug = re.sub(r"['’‘]", "", slug)
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    return slug


def resolve_aat_uri(raw_material: str) -> str | None:
    """Return Getty AAT URI for a material string, or None if not mapped."""
    if not raw_material:
        return None
    for key, uri in MATERIAL_AAT.items():
        if key.lower() in raw_material.lower():
            return uri
    return None


def make_artist(
    name: str,
    country: str = "",
    city: str = "",
    nationality: str = "",
    bio: str = "",
    birth_year: int | None = None,
    death_year: int | None = None,
    wikidata_qid: str | None = None,
    ulan_id: str | None = None,
    viaf_id: str | None = None,
    instagram: str | None = None,
    tags: list | None = None,
    themes: list | None = None,
    materials: list | None = None,
    living: bool = True,
    rating: int = 0,
    featured: bool = False,
    mould: bool = False,
    artworks: list | None = None,
    avatar: str | None = None,
    avatar_credit: str | None = None,
) -> dict:
    """Return a new artist record with all fields that sculptors.json expects."""
    artist_id = slugify(name)
    return {
        "id": artist_id,
        "name": name,
        "country": country,
        "city": city,
        "nationality": nationality,
        "bio": bio,
        "avatar": avatar,
        "avatar_credit": avatar_credit,
        "featured": featured,
        "rating": rating,
        "living": living,
        "mould": mould,
        "birth_year": birth_year,
        "death_year": death_year,
        "instagram": instagram,
        "wikidata_qid": wikidata_qid,
        "ulan_id": ulan_id,
        "viaf_id": viaf_id,
        "tags": tags or [],
        "themes": themes or [],
        "materials": materials or [],
        "artworks": artworks or [],
    }


def make_artwork(
    artist_id: str,
    seq: int,
    title: str,
    year: int | None = None,
    material: str = "",
    style: str = "",
    description: str = "",
    image: str | None = None,
    video: str | None = None,
    width_cm: float | None = None,
    height_cm: float | None = None,
    depth_cm: float | None = None,
    weight_kg: float | None = None,
    base_height_cm: float | None = None,
    edition_number: int | None = None,
    edition_size: int | None = None,
    foundry: str | None = None,
    patination: str | None = None,
    cast_date: str | None = None,
    material_aat_uri: str | None = None,
    technique_aat_uri: str | None = None,
    location_country: str | None = None,
    license: str | None = None,
    wikidata_qid: str | None = None,
    model_3d_url: str | None = None,
    model_3d_format: str | None = None,
) -> dict:
    """Return a new artwork record with all fields that sculptors.json expects."""
    if material_aat_uri is None and material:
        material_aat_uri = resolve_aat_uri(material)
    return {
        "id": f"{artist_id}-{seq:02d}",
        "title": title,
        "year": year,
        "material": material,
        "style": style,
        "image": image,
        "video": video,
        "description": description,
        "width_cm": width_cm,
        "height_cm": height_cm,
        "depth_cm": depth_cm,
        "weight_kg": weight_kg,
        "base_height_cm": base_height_cm,
        "edition_number": edition_number,
        "edition_size": edition_size,
        "foundry": foundry,
        "patination": patination,
        "cast_date": cast_date,
        "material_aat_uri": material_aat_uri,
        "technique_aat_uri": technique_aat_uri,
        "location_country": location_country,
        "license": license,
        "wikidata_qid": wikidata_qid,
        "model_3d_url": model_3d_url,
        "model_3d_format": model_3d_format,
        "views": [],
    }
