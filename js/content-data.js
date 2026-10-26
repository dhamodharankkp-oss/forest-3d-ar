/**
 * Forest Expedition Content Configuration
 * Configured with the requested Species and Threats:
 * Species: Spotted Deer, Indian Peacock, Royal Bengal Tiger, Indian Wild Boar, Indian Giant Flying Squirrel
 * Threats: Forest Fire, Wire Snares, Plastic Trash, Illegal Logging, Chemical Waste
 */
const FOREST_DATA = {
  title: "Reveal the Hidden Forest — Educational 3D Expedition",
  tagline: "Explore the ancient woodland, identify native wildlife species, and uncover ecological threats.",
  
  species: [
    {
      id: "spotted_deer",
      name: "Spotted Deer (Chital)",
      scientificName: "Axis axis",
      type: "species",
      icon: "🦌",
      rarity: "Keystone Herbivore",
      badge: "Forest Grazer",
      model: "assets/models/realistic_deer.glb",
      targetHeight: 2.3,
      position: { x: 0, z: -18 },
      image: "assets/deer_sample.jpg",
      description: "A graceful deer characterized by its golden rufous coat dotted with permanent white spots. Chital feed on tender grasses, fallen flowers, and fruits, maintaining the open structure of woodland glades.",
      ecologicalRole: "Primary herbivore consumer and vital prey base for apex predators like tigers and leopards.",
      conservationStatus: "Least Concern (IUCN)",
      discoveryClue: "Look near the sunlit central glade right beside the large mossy fallen hollow log."
    },
    {
      id: "peacock",
      name: "Indian Peafowl (Peacock)",
      scientificName: "Pavo cristatus",
      type: "species",
      icon: "🦚",
      rarity: "Avian Resident",
      badge: "National Bird",
      model: "assets/models/peacock.glb",
      modelScale: 1.4,
      position: { x: -28, z: -12 },
      description: "Famed for the male's spectacular iridescent blue-green neck plumage and elongated upper tail covert train shimmering with colorful 'eye-spots' (ocelli). They produce loud, resonant calls heard miles away.",
      ecologicalRole: "Omnivorous seed disperser and natural pest controller of venomous snakes, lizards, and insect swarms.",
      conservationStatus: "Least Concern (Protected under Wildlife Protection Act)",
      discoveryClue: "Perched proudly atop the mossy flat rock shelf to the west of the central path."
    },
    {
      id: "tiger",
      name: "Royal Bengal Tiger",
      scientificName: "Panthera tigris tigris",
      type: "species",
      icon: "🐅",
      rarity: "Apex Predator",
      badge: "Endangered Keystone",
      model: "assets/models/tiger.glb",
      modelScale: 1.6,
      position: { x: 42, z: -35 },
      ar: {
        enabled: true,
        title: "Royal Bengal Tiger",
        habitat: "bamboo_clearing",
        defaultScale: "1:1",
        lengthMeters: 2.9,
        shoulderHeightMeters: 1.15,
        hasTrees: true,
        treeType: "ancient_hardwood"
      },
      description: "The largest wild feline in the world, recognizable by its reddish-orange coat with dark vertical stripes. As solitary apex predators, they need vast contiguous tracts of healthy forest to hunt and thrive.",
      ecologicalRole: "Apex predator maintaining herbivore population balance, preventing overgrazing of forest ground flora.",
      conservationStatus: "Endangered (IUCN Red List)",
      discoveryClue: "Stalking stealthily beneath the dense bamboo and oak thickets across the eastern ridge."
    },
    {
      id: "wild_boar",
      name: "Indian Wild Boar",
      scientificName: "Sus scrofa cristatus",
      type: "species",
      icon: "🐗",
      rarity: "Ground Forager",
      badge: "Ecosystem Engineer",
      model: "assets/models/boar.glb",
      modelScale: 1.5,
      position: { x: -36, z: 28 },
      description: "A stocky mammal with a dark coarse bristly coat, a muscular mobile snout, and sharp protective lower tusks. Known for rooting through damp soil in search of roots, bulbs, and subterranean fungi.",
      ecologicalRole: "Acts as a natural 'plow' for the forest floor—their rooting churns compacted soil and buries tree seeds for germination.",
      conservationStatus: "Least Concern",
      discoveryClue: "Rooting through moist leaf humus in the shadowed hollow southwest of the trail."
    },
    {
      id: "flying_squirrel",
      name: "Indian Giant Flying Squirrel",
      scientificName: "Petaurista philippensis",
      type: "species",
      icon: "🐿️",
      rarity: "Arboreal Specialist",
      badge: "Canopy Glider",
      model: "assets/models/squirrel.glb",
      modelScale: 1.2,
      position: { x: 18, z: 24, y: 11.5 },
      description: "A large nocturnal arboreal rodent equipped with a fur-covered gliding membrane (patagium) stretching between limbs. It can glide over 50 meters between canopy branches silently.",
      ecologicalRole: "Specialist canopy frugivore that spreads high-canopy tree seeds and pollen across large forest gaps.",
      conservationStatus: "Least Concern",
      discoveryClue: "High up on the thick mossy branch of the towering elder oak tree to the southeast."
    }
  ],

  threats: [
    {
      id: "forest_fire",
      name: "Smoldering Forest Fire & Embers",
      type: "threat",
      severity: "CRITICAL HAZARD",
      icon: "🔥",
      model: "assets/models/forest_fire.glb",
      modelScale: 1.5,
      position: { x: 38, z: 18 },
      description: "An unextinguished campfire and smoldering brush generating thick smoke plumes and red-hot embers amidst dry dry-season leaf litter. A minor wind gust can engulf hundreds of forest acres.",
      impact: "Catastrophic destruction of canopy nesting trees, incineration of understory wildlife, and massive atmospheric carbon release.",
      remedy: "Immediately douse with sand and water until embers are cold; maintain permanent fire-break trenches.",
      discoveryClue: "Follow rising grey smoke columns and orange flickering embers near the dry rocky clearing."
    },
    {
      id: "wire_snare",
      name: "Concealed Poaching Wire Snare",
      type: "threat",
      severity: "CRITICAL CRIME",
      icon: "⚠️",
      model: "assets/models/wire_snare.glb",
      modelScale: 1.2,
      position: { x: -14, z: -34 },
      description: "A loop of high-tensile clutch wire anchored to a bent tree sapling along game trails. When a deer, boar, or predator steps through, it contracts with brutal force, causing amputation or slow death.",
      impact: "Indiscriminate mutilation and painful killing of endangered animals and non-target wildlife.",
      remedy: "Immediate snip and deactivation by anti-poaching squad, forensic patrol tracking, and sensor camera traps.",
      discoveryClue: "Concealed across a narrow deer game trail between the cluster of elder pine trees."
    },
    {
      id: "plastic_trash",
      name: "Non-Biodegradable Plastic Trash Dump",
      type: "threat",
      severity: "HIGH POLLUTION",
      icon: "🚯",
      model: "assets/models/plastic_trash.glb",
      modelScale: 1.5,
      position: { x: 25, z: -38 },
      description: "Discarded single-use plastic bottles, wrappers, poly-bags, and food packaging left by visitors. Animals mistake plastic for food, causing fatal intestinal blockages.",
      impact: "Soil asphyxiation, deadly gut impaction in grazing wildlife, and microplastic contamination of streams.",
      remedy: "Strict zero-waste checkpoint bag screenings, regular clean-up drives, and community recycling incentives.",
      discoveryClue: "Dumped along the forest dry stream bed near the weathered grey boulders."
    },
    {
      id: "illegal_logging",
      name: "Illegal Timber Logging & Tree Felling",
      type: "threat",
      severity: "HABITAT DESTRUCTION",
      icon: "🪓",
      model: "assets/models/illegal_logging.glb",
      modelScale: 1.5,
      position: { x: -44, z: 6 },
      description: "Freshly cut ancient hardwood stump with heavy axe gashes, discarded log cuts, and sawdust. Unregulated felling breaks continuous canopy corridors needed by arboreal wildlife.",
      impact: "Severe habitat fragmentation, loss of canopy wildlife corridors, and devastating monsoon topsoil erosion.",
      remedy: "Acoustic chainsaw detectors, satellite deforestation alerts, and armed community forest patrols.",
      discoveryClue: "Look for an unnatural clearing with sawed stumps and an iron woodcutter axe wedged into timber."
    },
    {
      id: "chemical_waste",
      name: "Leaking Toxic Chemical Waste Drum",
      type: "threat",
      severity: "BIOHAZARD CRIME",
      icon: "☣️",
      model: "assets/models/chemical_waste.glb",
      modelScale: 1.5,
      position: { x: -22, z: -46 },
      description: "An abandoned, corroded metal drum with biohazard warnings illegally dumped in the forest, leaking luminescent toxic chemicals and heavy metals directly into the soil and aquifer.",
      impact: "Immediate poisoning of natural water springs, groundwater contamination, and plant necrosis in surrounding soil.",
      remedy: "Deploy hazardous materials (HAZMAT) containment unit, seal and remove drum, and remediate tainted soil with bio-absorbent clay.",
      discoveryClue: "Located in the secluded ravine to the northwest, surrounded by a toxic puddle and dead vegetation."
    }
  ]
};

// Export for module or global use
if (typeof module !== "undefined" && module.exports) {
  module.exports = FOREST_DATA;
}
