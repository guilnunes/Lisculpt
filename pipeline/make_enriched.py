"""One-time script: applies editorial metadata to wikidata_raw.json → enriched.json."""
import json
from pathlib import Path

raw = json.loads(Path("d:/GitHub/Lisculpt/pipeline/output/wikidata_raw.json").read_text(encoding="utf-8"))

editorial = {
  "Q447300": {
    "country": "United States", "city": "New York",
    "bio": "Kiki Smith makes figurative sculpture, printmaking, and drawing that centres on the body—its vulnerabilities, spirituality, and relationship to the natural world. Working in glass, bronze, paper, and wax, she draws on medieval imagery, fairy tales, and feminist discourse to create works of visceral intimacy.",
    "tags": ["Figurative", "Feminist", "Symbolic", "Narrative"],
    "themes": ["Human", "Nature", "Mythology"],
    "materials": ["Bronze", "Glass", "Wax", "Paper"],
    "rating": 9,
  },
  "Q2424825": {
    "country": "United States", "city": "Los Angeles",
    "bio": "Thomas Houseago makes large-scale figurative sculpture in plaster, bronze, and corten steel, channelling the expressionist legacies of Picasso, Giacometti, and tribal art into a raw, physically confrontational idiom. His towering figures and fractured heads command architectural space with psychological weight.",
    "tags": ["Figurative", "Expressionist", "Monumental"],
    "themes": ["Human", "Psychological"],
    "materials": ["Plaster", "Bronze", "Steel"],
    "rating": 8,
  },
  "Q19800726": {
    "country": "Ghana", "city": "Tamale",
    "bio": "Ibrahim Mahama transforms discarded jute sacks—used to transport cocoa across West Africa—into vast sculptural installations that shroud public buildings and institutions. The accumulated labour and trade histories embedded in the material make visible the weight of postcolonial economic systems.",
    "tags": ["Installation", "Textile", "Political", "Conceptual"],
    "themes": ["Labour", "History", "Economy"],
    "materials": ["Mixed Media"],
    "rating": 8,
  },
  "Q3033213": {
    "country": "United States", "city": "New York",
    "bio": "Do Ho Suh creates translucent fabric replicas of domestic spaces—apartments, corridors, stairwells—that can be collapsed, shipped, and re-erected anywhere. The works interrogate the relationship between inhabitation and memory, displacement and belonging, personal history and collective architecture.",
    "tags": ["Installation", "Architectural", "Textile", "Conceptual"],
    "themes": ["Memory", "Home", "Identity"],
    "materials": ["Fabric", "Mixed Media"],
    "rating": 9,
  },
  "Q19509449": {
    "country": "United States", "city": "New York",
    "bio": "Arlene Shechet builds ceramic sculpture that resists tidiness—forms tilt, sag, and balance on invented plinths, as though caught mid-thought. Her practice in porcelain, stoneware, and bronze fuses historical craft traditions of Delft and Japanese ceramics with an improvisational, gestural sensibility.",
    "tags": ["Ceramic", "Abstract", "Gestural"],
    "themes": ["Form", "Balance", "Process"],
    "materials": ["Ceramics", "Bronze"],
    "rating": 7,
    "mould": True,
  },
  "Q6032604": {
    "country": "United States", "city": "New York",
    "bio": "Roxy Paine is best known for his Dendroid series—monumental stainless-steel trees that replicate the branching logic of organic growth through industrial fabrication. He also builds SCUMAK machines that autonomously extrude polyethylene blobs, exploring the intersection of natural systems and technological process.",
    "tags": ["Abstract", "Industrial", "Nature", "Conceptual"],
    "themes": ["Nature", "Technology", "Systems"],
    "materials": ["Steel", "Aluminum"],
    "rating": 7,
  },
  "Q5936654": {
    "country": "United States", "city": "Poughkeepsie",
    "bio": "Huma Bhabha constructs imposing figures from cork, clay, wire, and found objects, their surfaces scarred with Cycladic, African, and South Asian formal echoes. Her totemic works carry a persistent sense of trauma and resilience, standing at the convergence of ancient sculpture and postcolonial anxiety.",
    "tags": ["Figurative", "Totemic", "Mixed Media"],
    "themes": ["Human", "Trauma", "History"],
    "materials": ["Clay", "Mixed Media"],
    "rating": 8,
  },
  "Q7901287": {
    "country": "United States", "city": "Brooklyn",
    "bio": "Ursula von Rydingsvard carves cedar beams into monumental forms that evoke bowls, pods, and landscapes at architectural scale. Dusted with graphite to deepen their dark, furrowed surfaces, her sculptures carry the memory of displacement and rural labour across generations.",
    "tags": ["Monumental", "Organic", "Abstract"],
    "themes": ["Memory", "Nature", "Labour"],
    "materials": ["Wood", "Bronze"],
    "rating": 9,
    "mould": True,
  },
  "Q826213": {
    "country": "Belgium", "city": "Ronse",
    "bio": "Mark Manders stages his entire practice as an ongoing Self-Portrait as a Building—a fictional architecture populated by painted bronze figures, incomplete sentences, and arrested gestures. His uncanny tableaux fuse Surrealist logic with the quiet tension of a room mid-evacuation.",
    "tags": ["Conceptual", "Surrealist", "Figurative", "Installation"],
    "themes": ["Identity", "Psychological", "Language"],
    "materials": ["Bronze", "Wood", "Ceramics"],
    "rating": 9,
  },
  "Q1963864": {
    "country": "Germany", "city": "Berlin",
    "bio": "Nairy Baghramian makes elegantly discomfited sculpture—cast aluminium sections in flesh-like tones that slump against walls or sprawl across floors, suggesting prosthetics, furniture, or body parts on the verge of collapse. Her work questions the display conventions that normally uphold and frame objects.",
    "tags": ["Abstract", "Installation", "Conceptual"],
    "themes": ["Body", "Space", "Display"],
    "materials": ["Aluminum", "Wax"],
    "rating": 8,
  },
  "Q1578729": {
    "country": "Germany", "city": "Berlin",
    "bio": "Alicja Kwade manipulates everyday materials—clocks, stones, mirrors, wire—to probe time, value, and perception. Her spare, precise installations short-circuit familiar logic: a stone replaced by another of identical weight but opposite cost, a clock running backwards at the speed of the Earth's rotation.",
    "tags": ["Conceptual", "Installation", "Abstract"],
    "themes": ["Time", "Value", "Perception"],
    "materials": ["Stone", "Mixed Media"],
    "rating": 7,
  },
  "Q7777257": {
    "country": "United States", "city": "Chicago",
    "bio": "Theaster Gates works across ceramics, architecture, and social practice, using salvaged fire hoses, wooden beams, and slip-cast vessels as material carriers of Black American cultural history. His practice is inseparable from community infrastructure: he rebuilds neglected buildings on the South Side of Chicago as cultural venues.",
    "tags": ["Ceramic", "Social Practice", "Conceptual"],
    "themes": ["Community", "History", "Labour"],
    "materials": ["Ceramics", "Mixed Media"],
    "rating": 8,
    "mould": True,
  },
  "Q2900658": {
    "country": "India", "city": "New Delhi",
    "bio": "Bharti Kher uses the bindi—a mass-produced cosmetic dot worn on the forehead—as both material and symbol, applying thousands of them to fibreglass animals, mirrors, and canvases to question beauty, ritual, gender, and the layering of cultural identities. Her monumental animal sculptures carry quiet, loaded intensity.",
    "tags": ["Figurative", "Symbolic", "Mixed Media", "Feminist"],
    "themes": ["Identity", "Ritual", "Animal"],
    "materials": ["Fiberglass", "Mixed Media"],
    "rating": 8,
  },
  "Q17227429": {
    "country": "Kosovo", "city": "Berlin",
    "bio": "Petrit Halilaj makes sculpture and installation rooted in fragile personal and collective histories, from Kosovo's post-war rebuilding to queer intimacy under repression. His works—oversized insects, hand-embroidered stages, objects from his childhood bedroom—transform vulnerability into monumental tenderness.",
    "tags": ["Installation", "Narrative", "Personal", "Political"],
    "themes": ["Memory", "Identity", "Love"],
    "materials": ["Mixed Media"],
    "rating": 8,
  },
  "Q19998132": {
    "country": "Portugal", "city": "Barcelona",
    "bio": "Carlos Bunga constructs temporary architectural interventions from cardboard boxes and adhesive tape, transforming gallery spaces into labyrinthine enclosures he then methodically destroys. The cycle of building and unbuilding makes the impermanence of structures—domestic, institutional, political—visceral and visible.",
    "tags": ["Installation", "Architectural", "Ephemeral", "Conceptual"],
    "themes": ["Structure", "Time", "Impermanence"],
    "materials": ["Mixed Media"],
    "rating": 7,
    "artworks": [],  # clear false-positive Tunga artwork
  },
  "Q273696": {
    "country": "United Kingdom", "city": "London",
    "bio": "Mona Hatoum transforms domestic and medical objects into instruments of unease—oversized kitchen graters, hospital beds laced with electric current, maps rendered in human hair. Her sculptures hold violence and tenderness in suspension, making the familiar feel precarious and the body perpetually under threat.",
    "tags": ["Installation", "Political", "Feminist", "Conceptual"],
    "themes": ["Body", "Home", "Power"],
    "materials": ["Steel", "Glass", "Mixed Media"],
    "rating": 9,
  },
  "Q7827716": {
    "country": "United States", "city": "Princeton",
    "bio": "Toshiko Takaezu closed the openings of her ceramic vessels to create sealed forms that became repositories for sound—small clay balls inside producing a gentle rattle. Drawing on Zen philosophy and her Japanese-American heritage, her moon jars and cylindrical forms balance meditative stillness with expressive surface.",
    "tags": ["Ceramic", "Abstract", "Zen", "Meditative"],
    "themes": ["Form", "Silence", "Nature"],
    "materials": ["Ceramics"],
    "rating": 9,
  },
  "Q16200002": {
    "country": "United States", "city": "Brooklyn",
    "bio": "Simone Leigh makes large-scale bronze and ceramic figures that are resolutely Black and female, fusing African architectural traditions—Bahian house-dresses, Dogon granary facades—with the American history of medicine's exploitation of Black women's bodies. Her 2022 Venice Biennale Golden Lion cemented her as a defining voice of contemporary sculpture.",
    "tags": ["Figurative", "Ceramic", "Feminist", "Monumental"],
    "themes": ["Identity", "Body", "History"],
    "materials": ["Bronze", "Ceramics"],
    "rating": 10,
    "mould": True,
  },
  "Q43387704": {
    "country": "Uganda", "city": "New York",
    "bio": "Leilah Babirye carves wood and builds ceramics into defiant portrait-heads of LGBTQ+ refugees, drawing on Ugandan visual traditions to make visible lives erased by state violence. Her expressive, mask-like figures bristle with found materials—bottle caps, wire, beads—and carry the intensity of protest and mourning.",
    "tags": ["Figurative", "Ceramic", "Political", "Activist"],
    "themes": ["Identity", "Diaspora", "Resistance"],
    "materials": ["Wood", "Ceramics", "Mixed Media"],
    "rating": 8,
  },
  "Q4947173": {
    "country": "Mexico", "city": "Oaxaca",
    "bio": "Bosco Sodi builds thick paintings and sculptural objects from pigment mixed with sawdust, earth, and cellulose paste that dry over months into cracked, geological surfaces. His work embraces accident and process: forms split and settle unpredictably, recording time and climate as material facts.",
    "tags": ["Abstract", "Gestural", "Process", "Ceramic"],
    "themes": ["Nature", "Process", "Material"],
    "materials": ["Clay", "Mixed Media"],
    "rating": 7,
  },
}

for record in raw:
    qid = record["wikidata_qid"]
    ed = editorial.get(qid, {})
    for k, v in ed.items():
        record[k] = v

out_path = Path("d:/GitHub/Lisculpt/pipeline/output/enriched.json")
out_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote {len(raw)} records to {out_path.name}")
