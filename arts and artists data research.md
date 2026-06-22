## Standards, Schemas, Ontologies, and Open Datasets for an International Sculpture Directory

This report maps the international landscape of art-metadata standards, ontologies, controlled vocabularies, institutional implementations, and open datasets — with a working bias toward what is actually implementable in a single‑file HTML + Supabase project ("Lisculpt") that wants to interoperate with museums, Google rich results, and Wikidata. The short answer for the impatient: **store records as Schema.org `VisualArtwork` JSON-LD in Supabase, reference Getty AAT/ULAN/TGN by URI, mint a Wikidata QID per artist/work where one exists, and design your data so you can re-emit it as Linked Art JSON-LD or LIDO XML when a museum partner asks.** Everything below explains why.

---

### 1. Metadata standards and schemas for artworks and artists

All of these standards address the same five core questions: *what is the object, who made it, when/where, what is it made of, and where is it now?* They differ in formality, intended consumer, and whether they were designed for the web or for the catalogue card.

| Standard | Maintainer | Format | Artwork attributes | Artist attributes | Sculpture fit | Adoption |
|---|---|---|---|---|---|---|
| CDWA | Getty | Conceptual guidelines (~540 categories) | Object type, materials/techniques, measurements, inscriptions, condition, location, provenance, exhibition history, related works, sources | Person/Corporate Body authority: name variants, life dates/places, nationality, roles, biography, related people | Excellent — explicit categories for "Materials and Techniques", physical description, multi-part works | Reference standard underlying CDWA Lite, LIDO, CCO; mostly used indirectly |
| CCO | VRA + ALA | Content rules (not a schema) | Rules for cataloguing title, work type, creator, date, location, measurements, materials, subject | Authority records for personal/corporate/geographic names | Strong — explicitly covers 3D objects, decorative arts | Widely used in US museums and visual-resources libraries |
| LIDO v1.1 (Dec 2021) | ICOM-CIDOC LIDO WG | XML schema | Object/work type, classification, title, inscriptions, materialsTech (materials + technique), measurements, eventSet (production, acquisition, use, etc.), subject, repository, rights | Actor with role, qualifier, life events, nationality | Excellent — event-centric; "production" event holds materials/technique; LIDO Handbook 2022 has a dedicated Painting and Sculpture handbook | High — main harvesting format for Europeana and the Deutsche Digitale Bibliothek; CC BY 4.0 schema |
| VRA Core 4 | Visual Resources Association + LoC | XML | Work, Image (surrogate) and Collection records; materialSet, measurementsSet, stylePeriod, culturalContext, worktype, subject | Agent element with role/dates | Good for 3D works; supports separate Image records for views, which matters for sculpture (multiple angles) | Used by image-resource departments (university slide libraries, museum photo archives) |
| Dublin Core / DCMI Terms | DCMI | RDF / XML / plain key-value | 15 core terms (title, creator, subject, description, date, type, format, source, identifier, rights, etc.) + DCMI Terms (~80) | Just `dc:creator`; no authority structure built in | Minimal — too coarse for sculpture-specific attributes; usable only as a baseline for harvest | Universal lowest common denominator; required for OAI-PMH |
| Schema.org `VisualArtwork` | W3C/Google/MS/Yahoo | JSON-LD / Microdata / RDFa | `name`, `artform` (Painting/Sculpture/Print/...), `artMedium`, `artworkSurface`, `artEdition`, `width/height/depth`, `dateCreated`, `creator`, `image`, `material`, `keywords`, `locationCreated` | `Person` with `birthDate`, `deathDate`, `birthPlace`, `nationality`, `sameAs` (URI), `image`, `description` | Good and improving — `artform: "Sculpture"`, `artEdition` covers cast editions, supports `depth`. Weakness: no native foundry, patina, plinth fields | Universal on the public web; powers Google Knowledge Panel / rich results |
| MARC 21 / MODS | Library of Congress | MARC binary or MODS XML | 245 title, 100 author, 264 production, 300 physical description, 520 summary, 655 genre/form | Authority via LCNAF | Weak — bibliographic-centric; museums rarely use it for sculpture itself, but it's relevant for catalogues raisonnés | Library systems and union catalogues (WorldCat); MODS used in some hybrid art libraries |
| SPECTRUM 5.1 | Collections Trust (UK) | Procedural standard | Defines 21 "primary procedures" (object entry, location, condition, loan, etc.) with required information units mapped to CDWA/CIDOC CRM | Person/organization authority units | Generic — covers all material culture including sculpture, ceramics, furniture | Mandatory baseline for UK Accredited museums; widely used in Commonwealth |
| EAD 3 | Society of American Archivists + LoC | XML | Multilevel finding aid: fonds → series → file → item. Useful for artists' archives, studio papers, sketchbooks, plaster models in storage | Creator (corpname/persname/famname) at any level | Indirect — describes sculptors' *archives* and working models, not the bronzes themselves | Universal in archives |

**Practical reading:** for a web-first project, the only mandatory layer is **Schema.org `VisualArtwork` JSON-LD** (Google requires it for any chance of rich results). LIDO is the lingua franca for museum-to-aggregator data exchange; CDWA/CCO are the rule books behind it. Dublin Core is your fallback for OAI-PMH harvesting if a researcher ever asks. The Schema.org `artMedium` definition explicitly lists *Marble, Intaglio, Woodcut, DryPoint, Lithograph*, which already covers most adjacent craft media on the directory's scope.

---

### 2. Ontologies and conceptual models

Where the §1 standards say *what fields to put in a record*, ontologies say *what is true about the world and how facts relate.*

**CIDOC CRM (ISO 21127:2023, current version 7.1.3, Feb 2024)** is the canonical event-centric ontology. Instead of "Object → has-material → Bronze", CRM models a *Production event* (E12) that *used* (P16) bronze (E57) and *was carried out by* (P14) an actor (E21). This is verbose but lossless: it can represent that Rodin *designed* the model, Rudier *cast* the bronze in 1925, and the Musée Rodin *acquired* it in 1955 as three distinct events. This matters for sculpture more than any other medium because casts, foundries, patinations, and re-casts are first-class historical events.

**LRMoo v1.0 (April 2024)** supersedes FRBRoo 2.4 and harmonizes the museum CRM with the library IFLA-LRM. It distinguishes Work → Expression → Manifestation → Item. For sculpture this is useful for *cast editions*: the Work is "The Thinker"; each numbered bronze is an Item of a Manifestation. Lisculpt probably does not need full LRMoo, but the conceptual distinction (idea / edition / specific cast) should appear in the data model.

**Linked Art** is a JSON-LD application profile of CIDOC CRM 7.1.3 maintained by Getty, Yale, Rijksmuseum, NGA Washington, MoMA, V&A, Smithsonian, Louvre, Met, Frick, Philadelphia, and others (the consortium). Reached version 1.0 in 2023. It uses the Getty Vocabularies (AAT/ULAN/TGN) as core identity sources and is the practical, developer-friendly way to publish CRM-based data today. Compared to raw CRM, it hides `E22_Human-Made_Object` behind a JSON key like `HumanMadeObject` and `P45_consists_of` behind `made_of`. Documentation: https://linked.art/model/ and https://linked.art/api/1.0/.

**Europeana Data Model (EDM)** is the aggregator schema behind europeana.eu. It wraps a `ProvidedCHO` (cultural heritage object) inside an `ore:Aggregation` (from OAI-ORE) together with surrogate images (`edm:WebResource`) and a provider. It is more flexible than Dublin Core but less expressive than CRM. Sculpture-specific attributes go in `dc:medium`, `dcterms:extent`, and an open `edm:hasType` URI (typically pointing to AAT).

**ArCo** (Architettura della Conoscenza, 2018→) is the Italian Ministry of Culture's network of ontologies built on top of CIDOC CRM, modelling the ICCD catalogue records. It is the most expressive existing model for sculpture and decorative arts because it inherits ICCD's traditionally fine-grained Italian cataloguing categories (e.g., explicit slots for *materia e tecnica*, *patina*, *base/piedistallo*). Endpoint: https://dati.beniculturali.it/sparql.

**Wikidata's de-facto ontology for artworks** is informal but stable. Core item classes include **Q860861 (sculpture)**, **Q3305213 (painting)**, **Q11060274 (print)**, **Q14745 (ceramic art)**, **Q14897293 (mask)**, **Q14860489 (piece of furniture)**. Core properties: **P31 instance of**, **P170 creator**, **P186 material used**, **P2079 fabrication method**, **P571 inception**, **P276 location**, **P217 inventory number**, **P2048 height**, **P2049 width**, **P5524 depth**, **P88 commissioned by**, **P195 collection**, **P1071 location of creation**, **P1684 inscription**, **P1257 Iconclass notation**, **P1014 AAT ID**, **P245 ULAN ID**, **P1015 BIBSYS**, **P214 VIAF ID**, **P650 RKDartists ID**. For artists: **P569/P570 birth/death date**, **P19/P20 places**, **P27 country of citizenship**, **P106 occupation (sculptor = Q1281618)**, **P135 movement**.

**BIBFRAME 2.0** (LoC's MARC successor) handles bibliographic resources. Useful for Lisculpt only as a *target* when linking to catalogues raisonnés or monographs about a sculptor.

**Event-centric vs object-centric trade-off.** Object-centric models (Dublin Core, Schema.org, the Wikidata "single statement") are easy to store in a flat database row: one record, many columns. Event-centric models (CIDOC CRM, LIDO, Linked Art) require a graph or nested JSON because each fact is a node. *Pragmatic stance for Lisculpt:* store flat in Supabase Postgres; for each work also store a `jsonb` column holding a Linked Art–shaped representation if/when you want to publish. Postgres `jsonb` handles this cleanly and you can index it with GIN.

---

### 3. Controlled vocabularies and authority files

| Vocabulary | Maintainer | Scope | Sculpture/craft coverage | Access |
|---|---|---|---|---|
| Getty AAT | Getty Research Institute | ~500k concepts: materials, techniques, object types, styles | **Best for sculpture/ceramics/engraving/furniture techniques**: e.g., bronze casting (300053980), lost-wax process (300053917), raku ware (300133486), intaglio (300041379), etching (300053241), aquatint (300053180), woodcut (300041405), marquetry (300053884), patination (300053059), kiln-firing (300053123), joinery (300053973) | LOD: https://vocab.getty.edu/aat/ ; SPARQL endpoint; downloadable as N-Triples (ODC-BY 1.0) |
| Getty ULAN | Getty | ~800k+ artist/agent records with birth/death dates, places, nationality, roles | Sculptors, ceramists, printmakers, cabinetmakers, mask makers all have entries | https://vocab.getty.edu/ulan/ |
| Getty TGN | Getty | Geographic places, hierarchical | Useful for `locationCreated` and provenance | https://vocab.getty.edu/tgn/ |
| Getty CONA | Getty | Authoritative artwork identifiers | Coverage still partial but growing; useful for famous sculptures | https://vocab.getty.edu/cona/ |
| Iconclass | RKD / Brill | ~28k iconographic-subject codes (e.g., 11H(JEROME) = St Jerome) | Critical for figurative sculpture and religious imagery on ceramics | http://iconclass.org/ ; SKOS download |
| LCSH / LCNAF | Library of Congress | Subject and name authorities | Generic and library-flavoured; weaker for craft techniques than AAT | https://id.loc.gov/ |
| VIAF | OCLC | Cluster of national authority files (LCNAF, BnF, GND, NDL, etc.) | Excellent for identifying artists across language regions | https://viaf.org/ |
| Wikidata QIDs | Wikimedia | Universal identifier hub | Best practical hub: every Wikidata artist item already links to ULAN, VIAF, RKDartists, LCNAF, ISNI | SPARQL https://query.wikidata.org/ ; CC0 |
| RKDartists | Netherlands Institute for Art History | ~350k artist records, very strong for Northern European art | Detailed biographies, exhibition history | https://rkd.nl/en/explore/artists |

**Vocabulary recommendation for sculpture-adjacent crafts:** AAT is the only vocabulary with rich, granular coverage across all four sub-domains in scope. Reference AAT URIs in `artMedium`, `artform`, and a custom `technique` field. For artists, link both ULAN (canonical) and Wikidata QID (universal). The Met's collection API already publishes AAT URIs in its `tags` element and Wikidata URIs in `objectWikidata_URL`, providing a working template.

---

### 4. Institutional adoption — who uses what

| Institution | Internal/published schema | Ontology / LOD | Vocabularies used |
|---|---|---|---|
| The Met | Internal "CRD" cataloguing system → public REST JSON API | Linked Art member; tags include AAT URIs and Wikidata URIs in API responses | AAT, ULAN, Wikidata |
| Rijksmuseum | Internal Adlib/Axiell → OAI-PMH (LIDO-ish), REST, RDF endpoint | Publishes data in **both EDM and Linked Art**; Linked Art member | AAT, RKDartists, GeoNames |
| MoMA | Internal TMS → GitHub CSV/JSON dumps | Linked Art member (publishing in development) | Wiki QID and Getty ULAN ID embedded in artists dataset |
| Tate | Was TMS → static GitHub dump (snapshot frozen Oct 2014); newer API not public | None public; uses internal subject taxonomy | Subject hierarchy "people / places / nature / abstract concepts" |
| V&A | Internal CMS → REST API (rebuilt in 2022 with IIIF presentation manifests) | IIIF 3.0; AAT mapping in progress | AAT, ULAN, internal "category" vocab |
| Louvre | Internal MuseumPlus → collections.louvre.fr | Linked Art member, RDF endpoint in roadmap | AAT, ULAN, Joconde |
| Smithsonian (incl. SAAM, Freer/Sackler, Cooper Hewitt) | EDAN content repository | **SAAM publishes CIDOC CRM RDF at a SPARQL endpoint** (edan.si.edu/saam/sparql); Linked Art member | CIDOC CRM types, AAT, ULAN |
| National Gallery of Art (Washington) | Internal TMS → REST API, GitHub dump | Linked Art member, publishes Linked Art JSON-LD | AAT, ULAN |
| J. Paul Getty Museum | Internal TMS → JSON API, public datasets | **Largest Linked Art publisher**; Getty Vocabularies are integral | AAT, ULAN, TGN, CONA |
| Cleveland Museum of Art | Internal → openaccess-api.clevelandart.org | Linked Art in roadmap | AAT/ULAN URIs in select fields |
| Art Institute of Chicago | Custom "data-aggregator" → api.artic.edu | IIIF Image API v2; partial AAT linking | AAT, ULAN, internal place vocab citing TGN |
| Europeana | Aggregator; harvests LIDO/EDM | **EDM is its native model** | Multilingual mapping to GEMET, Iconclass, AAT |
| Google Arts & Culture | Schema.org `VisualArtwork` ingest + partner feeds (typically LIDO or museum-specific) | Schema.org → Google Knowledge Graph | Whatever the partner supplies |
| Wikidata / Wikimedia Commons | RDF; ad-hoc property set described in §2 | Open ontology of QIDs | Self-referential + structured-data-on-Commons for image metadata |

---

### 5. Open datasets — APIs, licenses, sizes

All sizes are total collection records; sculpture-specific subsets must be filtered with `classification`/`type` parameters because none of these museums publishes a sculpture-only dump.

| Institution | Endpoint / dump | License | Commercial reuse | Records (total) | Sculpture coverage |
|---|---|---|---|---|---|
| The Met | https://collectionapi.metmuseum.org/public/collection/v1/ ; https://github.com/metmuseum/openaccess | **CC0** (data + public-domain images) | Yes | 470,000+ artworks, 406,000+ CC0 images | "European Sculpture and Decorative Arts" department + sculpture throughout Greek/Roman, Asian, Arts of Africa/Oceania/Americas — filter `classification=Sculpture` for ~6,000+ records |
| Rijksmuseum | https://data.rijksmuseum.nl/ — REST API (key required), OAI-PMH, EDM + Linked Art dumps | **CC0** for descriptions; images public domain | Yes | 800,000+ objects | "Sculpture" object type filter; thousands of records including the famous wood/ivory carvings |
| MoMA | https://github.com/MuseumofModernArt/collection (CSV + JSON) | **CC0** for data; images licensed via Art Resource/Scala | Data: yes; images: no | ~140,000 artworks, ~15,833 artists | Classification "Sculpture" filter; especially strong for 20th–21st-c. work |
| Tate | https://github.com/tategallery/collection — **archived Oct 2014, no longer updated** | **CC0** data; images: image-by-image licence (often CC BY-NC-ND or restricted) | Data: yes; images: usually no | ~70,000 artworks frozen, ~3,500 artists | Snapshot only; Tate's modern API exists internally but is not public |
| V&A | https://api.vam.ac.uk/v2/ + IIIF | Data: **not CC0** — V&A terms allow personal/educational; commercial use requires licence | Restricted | 1.2M+ records, 750k+ images, 470k IIIF manifests | Strong in furniture, ceramics, metalwork; sculpture broadly defined |
| Louvre | https://collections.louvre.fr/ + downloadable CSV | Open Licence Etalab (≈CC BY) | Yes with attribution | 482,000+ records | Significant sculpture department (Roman, Renaissance, French) |
| Smithsonian | https://api.si.edu/openaccess/api/v1.0/ (api.data.gov key) + https://github.com/Smithsonian/OpenAccess | **CC0** | Yes | 4.5M+ CC0 records (growing from 2.8M at 2020 launch) across 21 units; SAAM also offers CIDOC CRM SPARQL at edan.si.edu/saam/sparql | SAAM, Hirshhorn (modern sculpture), Cooper Hewitt (decorative arts), African Art mask collections |
| National Gallery of Art (Washington) | https://github.com/NationalGalleryOfArt/opendata + Linked Art JSON-LD | **CC0** for both data and PD images | Yes | ~130,000 artworks | Filter `classification=Sculpture` |
| Cleveland Museum of Art | https://openaccess-api.clevelandart.org/ + https://github.com/ClevelandMuseumArt/openaccess | **CC0** | Yes | 64,000+ artwork records, 37,000+ images | Strong in Asian and medieval sculpture, ceramics, ivories |
| Art Institute of Chicago | https://api.artic.edu/api/v1/ + https://github.com/art-institute-of-chicago/api-data (S3 dump ~2.5 GB extracted) | Artwork data **CC0**; place data CC BY (from Getty TGN); 50,000+ images CC0 | Yes | Full collection; CC0 image subset 50,000+ | "Sculpture" classification filter |
| Europeana | https://api.europeana.eu/record/v2/ (key required) | Metadata: **CC0**; images: per provider | Metadata: yes | 50M+ items aggregated | "TYPE:3D" facet returns 3D/sculpture works from across hundreds of providers |
| Wikidata | https://query.wikidata.org/sparql | **CC0** | Yes | ~110M items; ~600k+ items with P31=sculpture (Q860861) as of 2025 | Universal — every artwork QID also serves as a join key for crosswalks |
| Getty Vocabularies LOD | https://vocab.getty.edu/ | **ODC-BY 1.0** (Open Data Commons Attribution) | Yes with attribution | AAT/ULAN/TGN/CONA dumps in N-Triples | Vocabulary, not artwork records |

---

### 6. Sculpture-specific and craft-specific considerations

**3D-specific attributes.** None of the mainstream schemas has a complete native vocabulary for what a sculpture cataloguer actually needs (depth/3D dimensions, weight, base/plinth, casting edition number, foundry mark, patination, installation requirements, orientation). Schema.org gives you `width/height/depth` and `artEdition`, but not foundry. LIDO solves this through repeatable `measurementsSet` (with `measurementType="depth"` or `"weight"`), and through `eventSet` of `lido:type="Production"` that can name a foundry as a participating actor. CIDOC CRM / Linked Art handle all of these natively because everything is just another event or a typed measurement. **Recommendation:** in your Supabase schema, store `width_cm`, `height_cm`, `depth_cm`, `weight_kg`, `base_height_cm`, `edition_number`, `edition_size`, `foundry`, `patination`, `installation_notes`, and `cast_date` as first-class columns. When you export to Schema.org you can flatten; when you export to LIDO/Linked Art you map them to typed measurement nodes and production-event participants.

**Ceramics.** Specialized fields rarely captured: firing temperature, atmosphere (oxidation/reduction), kiln type (anagama, noborigama, electric, wood), glaze recipe, clay body (porcelain/stoneware/earthenware), throwing vs hand-built. There is no widely adopted dedicated standard; AAT has all the *terms* (e.g., raku 300133486, celadon glaze 300013236), and ICCD's Italian *scheda OAC* (ceramic objects) is the most detailed national template. Use AAT-keyed free-text fields.

**Printmaking / engraving.** Edition size, edition number, state (proof, before/after letters), plate dimensions vs paper dimensions, signed/numbered status. Schema.org provides `artEdition` for total run, but state and proof type require AAT-tagged custom fields. LIDO and VRA Core both handle this with multiple `measurementsSet` (plate vs sheet) and a state field.

**Furniture.** Joinery (mortise-and-tenon, dovetail, marquetry), period style (Louis XV, Art Deco, mid-century modern), maker vs designer vs manufactory. AAT has terminology; the V&A's internal classification system is the de facto reference for decorative arts. No bespoke open standard.

**Masks.** Ritual function, cultural origin, ceremonial use vs theatrical, gender association, materials including non-permanent ones (feathers, raffia). Anthropological/ethnographic museums use SPECTRUM or LIDO with AAT subject terms; Iconclass adds iconography. For ethically sensitive provenance, Local Contexts notices (https://localcontexts.org/) are emerging as a standard practice and worth supporting in any modern directory.

**ICCD (Italy).** The Istituto Centrale per il Catalogo e la Documentazione defines numbered "scheda" templates per material type: *S* for sculpture, *OA* for objects of art, *OAC* for contemporary art, *RA* for archaeological finds, etc. They are exhaustively detailed and machine-readable as XML. ArCo exposes them as RDF. For sculpture, the *scheda S* is the most granular open template anywhere; Lisculpt would not implement it natively but could map to it for Italian institutional partners.

**3D scans and 3D metadata.** **IIIF 3D Technical Specification** is at editor's-draft / TR stage under the IIIF 3D Technical Specification Group (https://iiif.io/api/3d/), defining how to package GLTF/USDZ in IIIF manifests. **CARARE 2.0** (Connecting Archaeology and Architecture in Europeana, https://pro.europeana.eu/page/carare-schema) is the mature schema for heritage 3D and monuments, used to feed 3D content into Europeana, and includes fields for object geometry, surveying technique, and digital provenance of the scan. Sketchfab and the Smithsonian 3D viewer are the practical hosts; both accept CC0. **Recommendation for Lisculpt:** store a `model_3d_url` and a `model_3d_format` (gltf, glb, usdz, ply) per artwork, plus an optional IIIF 3D manifest URL — that future-proofs the directory without committing to a full CARARE implementation today.

---

### 7. Concrete record examples — same sculpture in three formats

The fictional record: *"Atlas Caído"* by Lygia Clark (1960), bronze, edition 3/8, cast 1962 at Fundição Ricardo, h 32 cm × w 28 cm × d 22 cm, private collection São Paulo.

**Schema.org `VisualArtwork` JSON-LD (recommended for Lisculpt storage and HTML embed):**

```json
{
  "@context": "https://schema.org",
  "@type": "VisualArtwork",
  "@id": "https://lisculpt.app/works/atlas-caido-1960",
  "name": "Atlas Caído",
  "artform": "Sculpture",
  "artMedium": "Bronze",
  "material": "http://vocab.getty.edu/aat/300010957",
  "artEdition": "8",
  "width":  { "@type": "Distance", "name": "28 cm" },
  "height": { "@type": "Distance", "name": "32 cm" },
  "depth":  { "@type": "Distance", "name": "22 cm" },
  "dateCreated": "1960",
  "creator": {
    "@type": "Person",
    "name": "Lygia Clark",
    "birthDate": "1920-10-23",
    "deathDate": "1988-04-25",
    "nationality": "Brazilian",
    "sameAs": [
      "https://www.wikidata.org/wiki/Q467019",
      "https://vocab.getty.edu/ulan/500115370"
    ]
  },
  "locationCreated": "Rio de Janeiro, Brazil",
  "image": "https://lisculpt.app/img/atlas-caido.jpg",
  "additionalProperty": [
    { "@type": "PropertyValue", "name": "edition_number", "value": "3/8" },
    { "@type": "PropertyValue", "name": "foundry", "value": "Fundição Ricardo" },
    { "@type": "PropertyValue", "name": "cast_date", "value": "1962" }
  ]
}
```

**Linked Art JSON-LD (recommended export for museum / Linked Art consumers):**

```json
{
  "@context": "https://linked.art/ns/v1/linked-art.json",
  "id": "https://lisculpt.app/works/atlas-caido-1960",
  "type": "HumanMadeObject",
  "_label": "Atlas Caído",
  "classified_as": [
    { "id": "http://vocab.getty.edu/aat/300047090", "type": "Type", "_label": "sculpture" }
  ],
  "identified_by": [
    { "type": "Name", "content": "Atlas Caído",
      "classified_as": [{ "id": "http://vocab.getty.edu/aat/300404670", "type": "Type", "_label": "preferred terms" }] }
  ],
  "made_of": [
    { "id": "http://vocab.getty.edu/aat/300010957", "type": "Material", "_label": "bronze" }
  ],
  "dimension": [
    { "type": "Dimension", "value": 32, "unit": { "id": "http://vocab.getty.edu/aat/300379098", "_label": "cm" },
      "classified_as": [{ "id": "http://vocab.getty.edu/aat/300055644", "_label": "height" }] },
    { "type": "Dimension", "value": 28, "unit": { "id": "http://vocab.getty.edu/aat/300379098" },
      "classified_as": [{ "id": "http://vocab.getty.edu/aat/300055647", "_label": "width" }] },
    { "type": "Dimension", "value": 22, "unit": { "id": "http://vocab.getty.edu/aat/300379098" },
      "classified_as": [{ "id": "http://vocab.getty.edu/aat/300072633", "_label": "depth" }] }
  ],
  "produced_by": {
    "type": "Production",
    "timespan": { "type": "TimeSpan", "begin_of_the_begin": "1960-01-01", "end_of_the_end": "1960-12-31" },
    "carried_out_by": [
      { "id": "https://vocab.getty.edu/ulan/500115370", "type": "Person", "_label": "Lygia Clark" }
    ],
    "technique": [
      { "id": "http://vocab.getty.edu/aat/300053917", "_label": "lost-wax casting" }
    ]
  }
}
```

**LIDO 1.1 XML (for OAI-PMH harvesting / Europeana ingestion):**

```xml
<lido:lido xmlns:lido="http://www.lido-schema.org">
  <lido:lidoRecID lido:type="local">lisculpt:atlas-caido-1960</lido:lidoRecID>
  <lido:descriptiveMetadata xml:lang="en">
    <lido:objectClassificationWrap>
      <lido:objectWorkTypeWrap>
        <lido:objectWorkType>
          <lido:conceptID lido:type="URI">http://vocab.getty.edu/aat/300047090</lido:conceptID>
          <lido:term>sculpture</lido:term>
        </lido:objectWorkType>
      </lido:objectWorkTypeWrap>
    </lido:objectClassificationWrap>
    <lido:objectIdentificationWrap>
      <lido:titleWrap>
        <lido:titleSet><lido:appellationValue>Atlas Caído</lido:appellationValue></lido:titleSet>
      </lido:titleWrap>
      <lido:objectMeasurementsWrap>
        <lido:objectMeasurementsSet>
          <lido:objectMeasurements>
            <lido:measurementsSet><lido:measurementType>height</lido:measurementType>
              <lido:measurementUnit>cm</lido:measurementUnit><lido:measurementValue>32</lido:measurementValue></lido:measurementsSet>
            <lido:measurementsSet><lido:measurementType>width</lido:measurementType>
              <lido:measurementUnit>cm</lido:measurementUnit><lido:measurementValue>28</lido:measurementValue></lido:measurementsSet>
            <lido:measurementsSet><lido:measurementType>depth</lido:measurementType>
              <lido:measurementUnit>cm</lido:measurementUnit><lido:measurementValue>22</lido:measurementValue></lido:measurementsSet>
          </lido:objectMeasurements>
        </lido:objectMeasurementsSet>
      </lido:objectMeasurementsWrap>
    </lido:objectIdentificationWrap>
    <lido:eventWrap>
      <lido:eventSet><lido:event>
        <lido:eventType><lido:term>Production</lido:term></lido:eventType>
        <lido:eventActor><lido:actorInRole>
          <lido:actor><lido:actorID lido:type="URI">https://vocab.getty.edu/ulan/500115370</lido:actorID>
            <lido:nameActorSet><lido:appellationValue>Lygia Clark</lido:appellationValue></lido:nameActorSet>
          </lido:actor>
        </lido:actorInRole></lido:eventActor>
        <lido:eventDate><lido:displayDate>1960</lido:displayDate></lido:eventDate>
        <lido:eventMaterialsTech><lido:materialsTech>
          <lido:termMaterialsTech><lido:term>bronze</lido:term>
            <lido:conceptID lido:type="URI">http://vocab.getty.edu/aat/300010957</lido:conceptID>
          </lido:termMaterialsTech>
        </lido:materialsTech></lido:eventMaterialsTech>
      </lido:event></lido:eventSet>
    </lido:eventWrap>
  </lido:descriptiveMetadata>
</lido:lido>
```

---

### 8. Practical recommendations for Lisculpt

**Storage layer (Supabase Postgres).** Use a normalized relational schema for `artworks`, `artists`, `materials`, `techniques`, plus a `jsonb` column `linked_art_doc` on each artwork that holds the Linked Art representation generated on save. This gives you fast SQL filtering for the web UI *and* near-zero-cost LOD export. Mandatory columns: title, artist_id, year_created (range), classification, width_cm, height_cm, depth_cm, weight_kg, edition_number, edition_size, foundry, patination, base_height_cm, material_aat_uri, technique_aat_uri, location_country, visibility (public/private/by-appointment), license.

**Identifiers.** For every artist, store `wikidata_qid`, `ulan_id`, `viaf_id` as nullable columns. For every artwork, mint your own UUID-based URI (`https://lisculpt.app/works/{slug}`) and store optional `wikidata_qid` and `cona_id`. This is the single most valuable interoperability decision: it lets you reconcile against the Met, Rijksmuseum, Wikidata, and Europeana automatically.

**Vocabulary references.** For materials, techniques, and object types, store the AAT URI rather than free text. For UI labels, dereference AAT once (it offers multilingual labels including Portuguese — important for a Brazilian product) and cache the labels in Supabase. This single discipline buys you internationalization, deduplication, and instant interoperability.

**Web markup.** On every artwork detail page, embed Schema.org `VisualArtwork` JSON-LD in a `<script type="application/ld+json">` tag exactly like the example above. This is what makes Google Knowledge Panel and Arts & Culture able to pick up your data with zero further work, and it is what makes Lisculpt indexable beyond Google (Yandex, Brave, Kagi all parse JSON-LD).

**Optional second feed — Linked Art JSON-LD.** Expose `https://lisculpt.app/works/{slug}.json` returning the Linked Art document via Supabase Edge Function. This costs little and immediately makes Lisculpt a peer of Yale, Rijksmuseum, NGA, Getty in the Linked Art ecosystem.

**Optional third feed — OAI-PMH / LIDO.** Only if a museum partner asks. Build it later by generating LIDO from your `linked_art_doc` (the two share CRM semantics, mapping is mechanical).

**Importing from museums.** A `crosswalks.ts` module mapping the Met API, Rijksmuseum, Cleveland, AIC, Smithsonian, and NGA JSON shapes into your internal schema will give Lisculpt a one-click "import reference work from museum X" feature — useful for editorial curation. All six of those APIs are CC0 on data and free of authentication friction except Rijksmuseum (free key).

**Things to design in from day one.** (a) A `views` table allowing multiple images per work (front/back/left/right/detail/installation) — sculpture demands this and Schema.org alone does not. (b) An `editions` table separate from `artworks` if you want to follow LRMoo properly and track individual casts. (c) A `provenance_event` table — chain of ownership is the single most commonly missing field in open datasets, and a sculpture-focused directory adds real value by capturing it. (d) Local Contexts notices for masks and culturally sensitive objects.

**What not to do.** Do not start by implementing CIDOC CRM directly — too verbose, no UX payoff. Do not store materials as free text — the cost of normalizing later is enormous. Do not use Dublin Core as your primary schema — it cannot express sculpture cleanly. Do not assume museum images are reusable; data is usually CC0 but image rights vary widely (Tate, V&A, MoMA all restrict images while releasing data freely).

**Summary stack:**

| Layer | Choice |
|---|---|
| Storage | Supabase Postgres, normalized + `jsonb` mirror |
| Wire format on the web | Schema.org `VisualArtwork` JSON-LD |
| Wire format for institutions | Linked Art JSON-LD (export) |
| Wire format for OAI-PMH | LIDO 1.1 XML (generated on demand) |
| Vocabularies | Getty AAT (materials, techniques, object types), Getty ULAN (artists), Getty TGN (places), Iconclass (subjects) |
| Identity hub | Wikidata QID per artist and per work where it exists; VIAF + ULAN as secondary |
| Images | IIIF 3.0 manifests if/when you scale; plain JPEG/WebP otherwise |
| 3D | Optional GLB/USDZ field per work; consider IIIF 3D manifest when the TR stabilises |

This stack gives Lisculpt international interoperability today (Google, Wikidata, Europeana via aggregator), peer-of-museums interoperability tomorrow (Linked Art, LIDO), and a flat-enough Supabase schema that a solo product-owner can ship it as a single-file HTML app this quarter.