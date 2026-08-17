#!/usr/bin/env python3
"""Generate projects.html from tools/projects.json.

The project database is the source of truth. It lives in tools/projects.json,
sanitised of contact details and monetary values because this repository is
public, and is regenerated from the spreadsheet export whenever the portfolio
changes.

Usage:
    python3 tools/projects_page.py
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _load():
    """Adapt the sanitised record shape to the column names used below."""
    data = json.load(open(os.path.join(ROOT, "tools", "projects.json"), encoding="utf-8"))["projects"]
    return [{
        "No.": p["no"], "Project Name": p["name"], "Description": p["description"],
        "Start": p["start"], "Duration (M)": p["duration_months"],
        "Appointment Type": p["appointment"], "Contract Format": p["contract_format"],
        "Status": p["status"], "Project Employer": p["employer"],
        "Consultant Company": p["consultant"], "Project Keywords": p["keywords"],
        "Branded products or materials used on ": p["materials"], "_band": p["band"],
    } for p in data]

import html, urllib.parse, datetime
from collections import Counter

BASE = "https://www.uniconsa.co.za"
DB = _load()

# Privacy: 'Contact', 'Email', and phone columns are deliberately NOT read here.
DROP = {"Contact", "Email", "Project Reference"}

def e(s): return html.escape(str(s), quote=True)
def img(repo, path, w=900):
    return (f"https://wsrv.nl/?url=raw.githubusercontent.com/chrisnott-unicon/"
            f"{repo}/main/{urllib.parse.quote(path)}&w={w}&output=webp&q=80")

def clean(s):
    if s is None: return ""
    s = re.sub(r"\s+", " ", str(s)).strip()
    return "" if s.lower() in ("none", "nan", "") else s

def yr(r):
    s = r.get("Start")
    return int(s[:4]) if isinstance(s, str) and len(s) >= 4 and s[:4].isdigit() else 0


# Display-only corrections for obvious typos in the source spreadsheet.
# (Source data should be corrected too — reported to the client.)
NAME_FIX = {
 "Angol America":"Anglo American",
 "JTR Ross Propoerty (Pty) Ltd":"JTR Ross Property (Pty) Ltd",
 "Nestle SA (Pty)Ltd":"Nestlé SA (Pty) Ltd",
 "Dr & Mrs De scally":"Dr & Mrs De Scally",
 "KZN Department Of Transport":"KZN Department of Transport",
 "Coega Development Corp.":"Coega Development Corporation",
 "uTugela Water Boards":"uThukela Water Board",
}
TITLE_FIX = {
 "Howick Main - New Retail Centre":"Howick Main Retail Centre",
 "Mangosuthu University of Technology – New Student Centre":"Mangosuthu University — Student Centre",
 "Nestle Coffee Factory – Upgrade & Additions":"Nestlé Coffee Factory Expansion",
 "Makhathini Drainage Canal near Jozini":"Makhathini Drainage Canal",
 "Kearsney College WTW Upgrade (V.O – Construction of New Clearwater Reservoir)":"Kearsney College WTW Upgrade",
 "Shorts Retreat Factory: Eco-Cycle Medical Waste Management":"Shorts Retreat Eco-Cycle Medical Waste Facility",
 "Woodcroft Cottage - Design & Construction of addition & Renovations":"Woodcroft Cottage — Additions & Renovations",
 "Completion of Phagindawo Junior School, Cato Ridge KZN":"Phagindawo Junior School, Cato Ridge",
 "Umgeni Water 61 Pipeline augmentation – chambers":"Umgeni Water 61 Pipeline Augmentation",
 "Hilton Veterinary Clinic - Upgrades & New MRI Scanner room":"Hilton Veterinary Clinic — MRI Suite",
 "Hilton Veterinary Clinic - Upgrades & New CT Scanner room":"Hilton Veterinary Clinic — CT Suite",
 "Merrivale Shell - Upgrade to Howzit Howick Fuel Station":"Merrivale Shell — Howzit Howick Fuel Station",
 "HOUSE RENCKEN - RENOVATIONS & ALTERATIONS":"House Rencken — Renovations & Alterations",
 "CDC 234/10 Isiphosemvelo Secondary School":"Isiphosemvelo Secondary School",
 "WS6059: Sankontshe 1Meg Concrete Reservoir":"Sankontshe 1ML Concrete Reservoir",
 "T2011-35 Ethembeni WTW":"Ethembeni Water Treatment Works",
}
def fixtitle(s):
    return TITLE_FIX.get(s, s)

def fixname(s):
    return NAME_FIX.get(s, s)

SECTORS = ["Bulk Water","Wastewater","Bridges & Heavy Civils","Commercial & Retail",
           "Industrial & Agri-Processing","Education","Healthcare","Residential & Estate"]
ICON = {"Bulk Water":"fa-water","Wastewater":"fa-recycle","Bridges & Heavy Civils":"fa-bridge-water",
        "Commercial & Retail":"fa-building","Industrial & Agri-Processing":"fa-industry",
        "Education":"fa-graduation-cap","Healthcare":"fa-house-medical","Residential & Estate":"fa-house"}

def sector_of(r):
    t = (clean(r.get("Project Name")) + " " + clean(r.get("Project Keywords")) + " " + clean(r.get("Description"))).lower()
    def has(*w): return any(x in t for x in w)
    if has("wwtw","sewer","sewerage","effluent","waste water","wastewater","medical waste"): return "Wastewater"
    if has("school","college","university","student centre","media centre","classroom"):     return "Education"
    if has("clinic","hospital","medical suite","veterinary","mri","ct scanner","x-ray"):      return "Healthcare"
    if has("bridge","canal","drainage","road bridge","services relocation","rti lot"):        return "Bridges & Heavy Civils"
    if has("abattoir","factory","steel","saw mill","depot","dairy","milking"):                return "Industrial & Agri-Processing"
    if has("mall","retail","shopping","fitout","fuel station","restaurant","shop","woolworths"): return "Commercial & Retail"
    if has("reservoir","water scheme","wtw","water treatment","pipeline","abstraction","filter",
           "waterworks","storage dam","bpt","water storage","water supply","chambers","pump station"): return "Bulk Water"
    if has("house","residential","housing","cottage","farm","driveway","estate"):             return "Residential & Estate"
    return "Bulk Water"

# ---- image pools -----------------------------------------------------------
B = "bestphotos"; EW = "Unicon-earthworks"; WT = "Unicon-Water-Treatment"; TP = "Unicon-tech-photos"
POOL = {
 "Bulk Water": [
   (B,"Unicon_Water_Reservoir_Dome_Roof_Concrete_Construction_Roof_Structure_20170218_Mountain_Landscape.jpg","Reinforced concrete dome roof on a circular water reservoir"),
   (B,"Unicon_Concrete_Dome_Pour_Reinforcement_Construction_Mountain_Landscape_20170325.jpg","Reservoir dome reinforcement ahead of a concrete pour"),
   (B,"Unicon-Construction-Water-Reservoir-Lining-Roof-20170325-Site-AerialView.jpg","Aerial view of reservoir lining and roof works"),
   (B,"Unicon_Construction_Circular_Concrete_Wall_Scaffolding_20170220.jpg","Scaffolding around a circular concrete reservoir wall"),
   (B,"Water_Reservoir_Construction_Site__Slangspruit Res20161208.jpg","Concrete reservoir under construction"),
   (B,"Unicon_Geomembrane_Lining_Installation_Sunset_Mountains_20170316.jpg","Geomembrane liner installation at sunset"),
   (B,"Unicon-Construction-Site-Resources-XYPEX-Rebar-Steel-Safety-Caps.jpg","Xypex crystalline waterproofing with capped reinforcing steel"),
   (B,"Unicon_Piping_Resources_Excavator_Crane_Pipeline_Installation_Construction_Site_Brown_Soil_Pipes_20260508_Africa_Howick.jpg","Pipeline installation with excavator and crane"),
 ],
 "Wastewater": [
   (B,"Unicon_Water_Treatment_Plant_Clarifier_Concrete_20181121.jpg","Concrete clarifier structure at a treatment plant"),
   (B,"Unicon-Environmental-Resources-Geomembrane-Liner-Installation-Construction-Site-October-2018.jpg","Geomembrane liner across a containment basin"),
   (B,"Construction-Site-Bidum-Geomembrane-Reedbeds-Wastewater Treatment-Club Med-Tinley Manor-Ballito-20250312.JPG","Geomembrane and bidum layers in reedbed wastewater cells"),
 ],
 "Bridges & Heavy Civils": [
   (B,"Unicon-Construction-Resources-Precast-Concrete-Bridge-Beam-Lift-20141210.jpg","Crane lifting a precast concrete bridge beam"),
   (B,"Unicon_Concrete_Pumping_Truck_Mixer_Steel_Rebar_Bridge_Deck_Pour_Resources_Drakensberg_Mountains_South_Africa_20150912.jpg","Bridge deck pour in the Drakensberg"),
   (B,"UniconSA_Rail_Overpass_Bridge_Construction_Crane.jpg","Rail overpass bridge under construction"),
   (B,"unicon-construction-bridge-installation-crane-lift.jpg","Bridge beam installation by crane"),
   (B,"Unicon_JCB_Excavator_Earthworks_Canal_RedSoil_Landscape_DSC_0034.JPG","Excavator shaping a canal through red soil"),
   (EW,"unicon-construction-aerial-excavation-earthmoving-site-IMG_5067.JPG","Aerial view of bulk excavation and earthmoving"),
 ],
 "Commercial & Retail": [
   (B,"construction-site-crane-building-scaffolding-Pietermaritzburg-Invesco Centre.JPG","Tower crane and scaffolding over a retail centre build"),
   (B,"Unicon-Construction-Resources-Steel-Frame-Building-Site-Groundwork-2026-05-08.JPG","Structural steel frame rising over groundworks"),
   (B,"Unicon-Manitou-Telehandler-Steel-Structure-Construction-Resource-Product-Building-Element-20190228.jpg","Telehandler positioning steel structure"),
   (B,"Unicon-Construction-Resources-Formwork-Steel-Structures-Building-Project-SouthAfrica-2008.jpg","Steel formwork and structural steelwork"),
 ],
 "Industrial & Agri-Processing": [
   (B,"unicon-construction-industrial-vessel-lift-installation.jpg","Crane lifting a large industrial vessel into position"),
   (B,"Cattle-Grazing-Foggy-Field-20220625.jpg","Dairy cattle grazing in a misty pasture"),
   (B,"Agrico_Pivot_Irrigation_System_20210830.jpg","Pivot irrigation system on farmland"),
   (B,"Unicon-VALLEY-irrigation-equipment-metal-framework-farm-field-2026-05-08.JPG","Irrigation equipment framework in the field"),
   (EW,"unicon-construction-agricultural-terracing-earthworks-site-dji-20241120.JPG","Agricultural terracing earthworks from the air"),
 ],
 "Education": [
   (B,"Construction-Workers-Building-Roof-Structure-Scaffolding-UniconSA.jpg","Workers erecting a roof structure on scaffolding"),
   (B,"Unicon-Scaffolding-RedMetal-ConcreteColumns-BuildingStructure-20140813.jpg","Scaffolding around concrete columns"),
   (B,"Unicon-Construction-Site-Reinforcement-Concrete-Rebar-Kearsney College-20150702.jpg","Steel reinforcement laid ahead of a concrete pour"),
 ],
 "Healthcare": [
   (B,"Unicon-Construction-Site-Building-Brick-Work-Materials-2026-05-08.JPG","Brickwork and materials on a current building site"),
   (B,"Unicon_Construction_Resources_Concrete_Pouring_Pillar_Formwork_Scaffolding_May_2026.jpg","Concrete poured into pillar formwork"),
   (B,"Unicon-Resources-Products-Brands-Building-Foundation-Concrete-Excavation-Eastern Cape-May-2018.jpg","Concrete foundation and excavation works"),
 ],
 "Residential & Estate": [
   (B,"Unicon_Construction_Workers_on_Concrete_Slab_Formwork.JPG","Workers finishing a concrete slab on formwork"),
   (B,"Unicon-Construction-Site-Building-Brick-Work-Materials-2026-05-08.JPG","Brickwork and building materials on site"),
   (B,"Unicon-Geocell-Retaining-Wall-Erosion-Control-Aggregate-Construction-Site-South-Africa-May-2026.jpg","Geocell retaining wall with aggregate fill"),
   (B,"Unicon_Construction_Resources_Concrete_Pouring_Pillar_Formwork_Scaffolding_May_2026.jpg","Concrete pour into pillar formwork"),
 ],
}

# Photographs whose filename explicitly identifies the project.
VERIFIED = {
 "Tinley Manor WWTW (Club Med Resort)":
   (B,"Construction-Site-Concrete-Pour-Reedbeds-Wastewater Treatment-Club Med-Tinley Manor-Ballito-20250312.JPG",
    "Concrete pour for the reedbed wastewater treatment works at Club Med Tinley Manor, Ballito"),
 "Invesco Shopping Mall – PMB":
   (B,"construction-site-crane-building-scaffolding-Pietermaritzburg-Invesco Centre.JPG",
    "Tower crane and scaffolding over the Invesco Centre construction site, Pietermaritzburg"),
 "Mkomazi River Bridge":
   (B,"Rural_Bridge_Over_Brown_River_Umkomazi_Rolling_Hills_South_Africa.jpg",
    "Road bridge spanning the Umkomazi river amid rolling hills"),
 "Bhobhoyi Water Treatment Upgrade":
   (B,"Clarifloculator_Reservoir_Construction_Site_Concrete_Structure_Rebar_Boyboyi_Port Shepstone_KZN_RSA_(2).jpg",
    "Clariflocculator reinforcement and concrete structure at Bhobhoyi, Port Shepstone"),
 "Kearsney College WTW Upgrade (V.O – Construction of New Clearwater Reservoir)":
   (B,"Unicon-Construction-Site-Reinforcement-Concrete-Rebar-Kearsney College-20150702.jpg",
    "Steel reinforcement for the clearwater reservoir at Kearsney College"),
}

FLAGSHIP = {
 "Howick Main - New Retail Centre",
 "Mnqumashe High Throughput Abattoir",
 "Invesco Shopping Mall – PMB",
 "Makhathini Drainage Canal near Jozini",
 "Mangosuthu University of Technology – New Student Centre",
 "Nestle Coffee Factory – Upgrade & Additions",
 "Thabazimbi 10ML Reservoir with Dome Roof",
 "Tinley Manor WWTW (Club Med Resort)",
}

# curated one-line "signature" notes, drawn from each project's own description
SIG = {
 "Howick Main - New Retail Centre":"7,600 m² retail GLA · Checkers, Dischem, Mr Price · 17 months",
 "Mnqumashe High Throughput Abattoir":"Cut-to-fill platforms · Portal-frame steel · Full mechanical install",
 "Invesco Shopping Mall – PMB":"17,000 m² over 3 storeys · Basement parking · All concrete structure",
 "Makhathini Drainage Canal near Jozini":"4 km concrete-lined canal · Mjindi Plantations farmland drainage",
 "Mangosuthu University of Technology – New Student Centre":"New student centre, Umlazi campus · Delivered in 10 months",
 "Nestle Coffee Factory – Upgrade & Additions":"Evaporator building · Cooling towers · 900 NB stormwater",
 "Thabazimbi 10ML Reservoir with Dome Roof":"10ML · Post-tensioned walls · Dome roof with no column supports",
 "Tinley Manor WWTW (Club Med Resort)":"New WWTW for the Club Med resort development",
}

# ---- build records ---------------------------------------------------------
recs = []
pool_idx = Counter()
for r in DB:
    status = clean(r.get("Status"))
    if status not in ("Complete", "In Progress"):
        continue
    raw_name = clean(r.get("Project Name"))
    name = fixtitle(raw_name)
    sec = sector_of(r)
    y = yr(r)
    dur = clean(r.get("Duration (M)"))
    try: dur = str(int(float(dur)))
    except Exception: dur = ""
    if raw_name in VERIFIED:
        repo, path, alt = VERIFIED[raw_name]; verified = True
    else:
        p = POOL[sec]; repo, path, alt = p[pool_idx[sec] % len(p)]; pool_idx[sec] += 1; verified = False
    recs.append(dict(
        name=name, raw_name=raw_name, sector=sec, year=y,
        decade=f"{(y//10)*10}s" if y else "",
        status=status, band=r["_band"],
        employer=fixname(clean(r.get("Project Employer"))) or "—",
        consultant=fixname(clean(r.get("Consultant Company"))) or "—",
        appt=clean(r.get("Appointment Type")), fmt=clean(r.get("Contract Format")),
        dur=dur, desc=clean(r.get("Description")),
        kw=clean(r.get("Project Keywords")),
        mats=clean(r.get("Branded products or materials used on ")),
        flagship=raw_name in FLAGSHIP, sig=SIG.get(raw_name, ""),
        repo=repo, path=path, alt=alt, verified=verified,
    ))

recs.sort(key=lambda x: (-x["year"], x["name"]))
DECADES = sorted({r["decade"] for r in recs if r["decade"]}, reverse=True)
BANDS = ["R50M+","R20–50M","R5–20M","Under R5M"]
nflag = sum(1 for r in recs if r["flagship"])
top_clients = Counter(r["employer"] for r in recs).most_common(6)

def note(r):
    return "" if r["verified"] else "\n            <!-- photo: representative of this discipline, not a verified photograph of this project -->"

def meta_row(label, value):
    return (f'<div class="flex justify-between gap-3"><dt class="font-mono text-[9px] uppercase tracking-widest text-gray-500">{label}</dt>'
            f'<dd class="text-right text-[10px] font-bold text-gray-200">{e(value)}</dd></div>')

# ---- flagship cards --------------------------------------------------------
flags = []
for r in [x for x in recs if x["flagship"]]:
    flags.append(f"""
          <article class="group relative flex flex-col overflow-hidden rounded-sm border border-gray-800 bg-[#111111] shadow-2xl transition-colors hover:border-unicon-green">{note(r)}
            <div class="relative aspect-[16/10] overflow-hidden">
              <img src="{img(r['repo'], r['path'], 900)}" alt="{e(r['alt'])}" loading="lazy" decoding="async"
                   class="h-full w-full object-cover grayscale-[35%] transition duration-700 group-hover:scale-[1.04] group-hover:grayscale-0">
              <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#050505] via-[#050505]/25 to-transparent"></div>
              <span class="absolute left-4 top-4 inline-flex items-center gap-2 rounded-sm border border-unicon-green/40 bg-[#050505]/85 px-3 py-1.5 text-[9px] font-bold uppercase tracking-[0.2em] text-unicon-green backdrop-blur-sm">
                <i class="fa-solid fa-star text-[8px]"></i> Flagship
              </span>
              <span class="absolute right-4 top-4 rounded-sm border border-gray-700 bg-[#050505]/85 px-3 py-1.5 font-mono text-[9px] uppercase tracking-widest text-gray-300 backdrop-blur-sm">{r['year']}</span>
              <div class="absolute inset-x-0 bottom-0 p-5 sm:p-6">
                <span class="mb-2 inline-flex items-center gap-1.5 rounded-sm bg-unicon-green/25 px-2 py-1 text-[9px] font-bold uppercase tracking-widest text-white backdrop-blur-sm">
                  <i class="fa-solid {ICON[r['sector']]} text-[9px]"></i>{e(r['sector'])}
                </span>
                <h3 class="clamp-3 text-lg font-extrabold uppercase leading-tight tracking-tight text-white sm:text-xl">{e(r['name'])}</h3>
              </div>
            </div>
            <div class="flex flex-1 flex-col p-5 sm:p-6">
              <p class="mb-4 text-sm font-light leading-relaxed text-gray-400">{e(r['desc'])}</p>
              {f'<p class="mt-4 border-l-2 border-unicon-green pl-3 font-mono text-[10px] uppercase tracking-widest text-gray-300">{e(r["sig"])}</p>' if r['sig'] else ''}
              <dl class="mt-auto space-y-1.5 border-t border-gray-800 pt-4">
                {meta_row("Employer", r["employer"])}
                {meta_row("Consultant", r["consultant"])}
                {meta_row("Contract scale", r["band"])}
                {meta_row("Duration", r["dur"] + " months") if r["dur"] else ""}
              </dl>
            </div>
          </article>""")

# ---- all project cards -----------------------------------------------------
cards = []
for r in recs:
    hay = " ".join([r["name"], r["raw_name"], r["sector"], r["employer"], r["consultant"], r["desc"],
                    r["kw"], r["mats"], str(r["year"]), r["band"], r["status"], r["appt"], r["fmt"]]).lower()
    live = r["status"] == "In Progress"
    status_badge = (f'<span class="inline-flex items-center gap-1.5 rounded-sm border border-amber-500/40 bg-amber-500/10 px-2 py-1 text-[8px] font-bold uppercase tracking-widest text-amber-400"><span class="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-400"></span>In progress</span>'
        if live else '<span class="rounded-sm border border-gray-700 px-2 py-1 text-[8px] font-bold uppercase tracking-widest text-gray-500">Complete</span>')
    fbadge = ('<span class="absolute left-3 top-3 inline-flex items-center gap-1.5 rounded-sm border border-unicon-green/40 bg-[#050505]/85 px-2 py-1 text-[8px] font-bold uppercase tracking-[0.2em] text-unicon-green backdrop-blur-sm"><i class="fa-solid fa-star text-[7px]"></i>Flagship</span>'
        if r["flagship"] else "")
    cards.append(f"""
          <article class="project-card group flex flex-col overflow-hidden rounded-sm border border-gray-800 bg-[#111111] transition-colors hover:border-unicon-green"
                   data-sector="{e(r['sector'])}" data-decade="{e(r['decade'])}" data-band="{e(r['band'])}"
                   data-flagship="{'1' if r['flagship'] else '0'}" data-search="{e(hay)}">{note(r)}
            <div class="relative aspect-[16/9] shrink-0 overflow-hidden">
              <img src="{img(r['repo'], r['path'], 700)}" alt="{e(r['alt'])}" loading="lazy" decoding="async"
                   class="h-full w-full object-cover grayscale-[40%] transition duration-700 group-hover:scale-[1.04] group-hover:grayscale-0">
              <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#111111] via-transparent to-transparent"></div>{fbadge}
              <span class="absolute right-3 top-3 rounded-sm border border-gray-700 bg-[#050505]/85 px-2 py-1 font-mono text-[9px] uppercase tracking-widest text-gray-300 backdrop-blur-sm">{r['year']}</span>
            </div>
            <div class="flex flex-1 flex-col p-5">
              <div class="mb-3 flex flex-wrap items-center gap-2">
                <span class="inline-flex items-center gap-1.5 rounded-sm bg-unicon-green/15 px-2 py-1 text-[9px] font-bold uppercase tracking-widest text-unicon-green">
                  <i class="fa-solid {ICON[r['sector']]} text-[9px]"></i>{e(r['sector'])}
                </span>
                {status_badge}
              </div>
              <h3 class="text-sm font-bold uppercase leading-tight tracking-tight text-white">{e(r['name'])}</h3>
              <p class="mt-3 flex-1 text-xs font-light leading-relaxed text-gray-400">{e(r['desc'][:230] + ('…' if len(r['desc'])>230 else ''))}</p>
              <dl class="mt-auto space-y-1 border-t border-gray-800 pt-3">
                {meta_row("Employer", r["employer"])}
                {meta_row("Consultant", r["consultant"]) if r["consultant"] != "—" else ""}
                {meta_row("Scale", r["band"])}
              </dl>
            </div>
          </article>""")

def chips(kind, values):
    return "".join(
        f"""
              <button type="button" data-filter="{kind}" data-value="{e(v)}"
                      class="chip rounded-sm border border-gray-700 px-3 py-2 text-[9px] font-bold uppercase tracking-widest text-gray-400 transition-colors hover:border-unicon-green hover:text-white">"""
        + (f'<i class="fa-solid {ICON[v]} mr-1.5 text-[9px]"></i>' if kind == "sector" else "")
        + f"{e(v)}</button>" for v in values)

GALLERY = [
 (B,"Unicon_Concrete_Dome_Pour_Reinforcement_Construction_Mountain_Landscape_20170325.jpg","Dome pour","Reservoir dome reinforcement, March 2017"),
 (B,"Unicon-Construction-Water-Reservoir-Lining-Roof-20170325-Site-AerialView.jpg","Reservoir aerial","Reservoir lining and roof, aerial view"),
 (B,"Unicon_Geomembrane_Lining_Installation_Sunset_Mountains_20170316.jpg","Liner install","Geomembrane installation at sunset"),
 (WT,"unicon_construction_clarifier_water_treatment_mechanical_Portshepstone_Bab_20170118_081735.jpg","Clarifier","Water treatment clarifier, Port Shepstone"),
 (B,"Water_Reservoir_Construction_Site__Slangspruit Res20161208.jpg","Reservoir build","Concrete reservoir construction, December 2016"),
 (B,"Unicon_Concrete_Pumping_Truck_Mixer_Steel_Rebar_Bridge_Deck_Pour_Resources_Drakensberg_Mountains_South_Africa_20150912.jpg","Deck pour","Bridge deck pour, Drakensberg, September 2015"),
 (B,"UniconSA_Rail_Overpass_Bridge_Construction_Crane.jpg","Rail overpass","Rail overpass bridge construction"),
 (B,"unicon-construction-bridge-installation-crane-lift.jpg","Beam lift","Bridge beam installation by crane"),
 (EW,"unicon-construction-aerial-excavation-earthmoving-site-IMG_5067.JPG","Mass earthworks","Aerial view of bulk excavation"),
 (EW,"unicon-construction-agricultural-terracing-earthworks-site-dji-20241120.JPG","Terracing","Agricultural terracing, November 2024"),
 (EW,"Unicon-Construction-earthworks-site-preparation-heavy-machinery-DJI-20241016.JPG","Site prep","Platform preparation, October 2024"),
 (TP,"unicon-construction-aerial-view-building-foundation-excavation-site-africa-johannesburg.PNG","Foundations","Aerial foundation works, Johannesburg"),
 (B,"Unicon-Construction-Site-Resources-XYPEX-Rebar-Steel-Safety-Caps.jpg","Xypex & rebar","Crystalline waterproofing with capped rebar"),
 (B,"Agrico_Pivot_Irrigation_System_20210830.jpg","Pivot irrigation","Agrico pivot irrigation, August 2021"),
 (B,"Unicon_Construction_Workers_on_Concrete_Slab_Formwork.JPG","Slab formwork","Workers finishing a concrete slab"),
 (TP,"Unicon Construction Architectural Planning and Site Consultation.jpg","Planning","Architectural planning and site consultation"),
]
gal = "".join(f"""
            <button type="button" class="gal-item group relative aspect-[4/3] overflow-hidden rounded-sm border border-gray-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-unicon-green"
                    data-full="{img(rp, pt, 1600)}" data-caption="{e(cap)}">
              <img src="{img(rp, pt, 500)}" alt="{e(cap)}" loading="lazy" decoding="async"
                   class="h-full w-full object-cover grayscale-[40%] transition duration-500 group-hover:scale-105 group-hover:grayscale-0">
              <span class="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-[#050505] to-transparent p-3 text-left text-[9px] font-bold uppercase tracking-widest text-white">{e(t)}</span>
            </button>""" for rp, pt, t, cap in GALLERY)

ld = {"@context":"https://schema.org","@type":"CollectionPage",
      "name":"Unicon Construction — Master Project Database",
      "url":f"{BASE}/projects.html",
      "description":f"{len(recs)} completed and in-progress projects delivered by Unicon Construction since 1991.",
      "hasPart":[{"@type":"CreativeWork","name":r["name"],"about":r["sector"],
                  "dateCreated":str(r["year"])} for r in recs]}

sector_counts = Counter(r["sector"] for r in recs)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chrome

# The nav and footer are owned by tools/chrome.py so this page cannot drift
# away from the rest of the site.
NAV = chrome.NAV_START + "\n" + chrome.nav("projects.html") + "\n    " + chrome.NAV_END
FOOTER = chrome.FOOT_START + "\n" + chrome.footer("projects.html") + "\n    " + chrome.FOOT_END

HTML = f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <!-- Google Tag Manager -->
    <script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
    new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
    j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
    'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
    }})(window,document,'script','dataLayer','GTM-59TZ364B');</script>
    <!-- End Google Tag Manager -->

    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>Project Database | {len(recs)} Civil &amp; Water Projects | Unicon</title>
    <meta name="description" content="Every Unicon project since 1991: post-tensioned reservoirs, water treatment works, provincial bridges and turnkey builds. Search {len(recs)} records by discipline.">
    <meta name="keywords" content="Unicon Construction Projects, Bulk Water Reservoirs, Post-Tensioned Reservoir, Water Treatment Works, Bridge Construction, Retail Centre Construction, South Africa, KwaZulu-Natal, UGU District Municipality, Umgeni Water">
    <link rel="canonical" href="{BASE}/projects.html">
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-TWWS9BQM18"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-TWWS9BQM18');
    </script>

    <link rel="icon" href="https://wsrv.nl/?url=raw.githubusercontent.com/chrisnott-unicon/UniconLogo/main/UniconBlk.png&amp;w=64&amp;h=64&amp;fit=contain&amp;output=png">
    <meta property="og:title" content="Unicon Construction | Master Project Database">
    <meta property="og:description" content="{len(recs)} projects delivered since 1991 — bulk water, heavy civils and turnkey construction across Southern Africa.">
    <meta property="og:image" content="https://raw.githubusercontent.com/chrisnott-unicon/bestphotos/main/unicon-construction-bridge-installation-crane-lift.jpg">
    <meta property="og:url" content="{BASE}/projects.html">
    <meta property="og:type" content="website">

    <script type="application/ld+json">
{json.dumps(ld, indent=2)}
    </script>

    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script>
        tailwind.config = {{
            theme: {{ extend: {{
                colors: {{ unicon: {{ black:'#0a0a0a', dark:'#1c1c1c', slate:'#f4f4f5', green:'#475c4d', border:'#e5e7eb' }} }},
                fontFamily: {{ sans:['"Century Gothic"','sans-serif'], mono:['ui-monospace','monospace'] }},
                letterSpacing: {{ tighter:'-0.04em', tight:'-0.02em', widest:'0.2em' }}
            }} }}
        }}
    </script>
    <style>
        body {{ background-color:#050505; color:#fff; -webkit-font-smoothing:antialiased; margin:0; padding:0; overflow-x:hidden; }}
        .bg-blueprint-dark {{ background-image:linear-gradient(to right,rgba(255,255,255,.05) 1px,transparent 1px),linear-gradient(to bottom,rgba(255,255,255,.05) 1px,transparent 1px); background-size:4rem 4rem; }}
        .text-outline {{ color:transparent; -webkit-text-stroke:1px #fff; }}
        @keyframes fadeUp {{ from {{ opacity:0; transform:translateY(20px);}} to {{ opacity:1; transform:translateY(0);}} }}
        .animate-fade-up {{ animation:fadeUp 1s cubic-bezier(.16,1,.3,1) forwards; opacity:0; }}
        .clamp-3 {{ display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }}
        .chip.is-active {{ background-color:#475c4d; border-color:#475c4d; color:#fff; }}
        .search-input:focus {{ box-shadow:0 0 15px rgba(71,92,77,.3); }}
        .whatsapp-fab {{ position: fixed; bottom: calc(30px + env(safe-area-inset-bottom) + var(--fab-lift, 0px)); right: 30px; background-color: #25D366; color: white; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 32px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); z-index: 9998; transition: transform 0.3s ease, bottom 0.3s ease; text-decoration: none; }}
        .whatsapp-fab:hover {{ transform: scale(1.1); }}
        @media (prefers-reduced-motion: reduce) {{ .animate-fade-up {{ animation:none; opacity:1; }} * {{ transition-duration:.01ms !important; }} }}
    </style>
</head>
<body class="font-sans selection:bg-unicon-green selection:text-white">
    <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-59TZ364B" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>

    <a href="#database" class="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[200] focus:rounded-sm focus:bg-unicon-green focus:px-4 focus:py-2 focus:text-xs focus:font-bold focus:uppercase focus:tracking-widest focus:text-white">Skip to project database</a>

    <a href="https://wa.me/27664834709?text=Hello%20Unicon,%20I%20would%20like%20to%20discuss%20a%20project." target="_blank" rel="noopener noreferrer" class="whatsapp-fab" aria-label="Chat with us on WhatsApp"><i class="fa-brands fa-whatsapp"></i></a>

{NAV}

    <header class="relative overflow-hidden border-b border-gray-800 bg-blueprint-dark pb-16 pt-32 md:pb-24 md:pt-40">
        <div class="absolute inset-0 opacity-[0.13]">
            <img src="{img(B,'unicon-construction-bridge-installation-crane-lift.jpg',1600)}" alt="" aria-hidden="true" class="h-full w-full object-cover grayscale">
        </div>
        <div class="relative z-10 mx-auto max-w-[90rem] animate-fade-up px-6 sm:px-8 lg:px-12">
            <div class="mb-6">
                <span class="inline-flex items-center gap-2 border border-gray-700 bg-[#111111] px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest text-white md:text-xs">
                    <span class="h-2 w-2 animate-pulse rounded-full bg-unicon-green"></span>Complete portfolio // 1991 – {max(r['year'] for r in recs)}
                </span>
            </div>
            <h1 class="text-[13vw] font-extrabold uppercase leading-[0.85] tracking-tighter sm:text-[9vw] lg:text-[6rem] xl:text-[7rem]">
                Built to <br><span class="text-outline">Outlast.</span>
            </h1>
            <p class="mt-8 max-w-3xl text-lg font-light leading-relaxed text-gray-400 md:text-xl">
                Every project Unicon has delivered since 1991 — {len(recs)} of them. Post-tensioned reservoirs holding megalitres without a drop lost, provincial bridges over live rivers, water schemes that reached communities who had none. Start with the flagships, then search the full record.
            </p>
            <div class="mt-12 grid grid-cols-2 gap-px overflow-hidden rounded-sm border border-gray-800 bg-gray-800 sm:grid-cols-4">
                <div class="bg-[#0a0a0a] p-5"><p class="text-2xl font-black tracking-tighter text-white md:text-3xl">{len(recs)}</p><p class="mt-1 font-mono text-[9px] uppercase tracking-widest text-gray-500">Projects Delivered</p></div>
                <div class="bg-[#0a0a0a] p-5"><p class="text-2xl font-black tracking-tighter text-white md:text-3xl">35</p><p class="mt-1 font-mono text-[9px] uppercase tracking-widest text-gray-500">Years Executing</p></div>
                <div class="bg-[#0a0a0a] p-5"><p class="text-2xl font-black tracking-tighter text-unicon-green md:text-3xl">R1.5B+</p><p class="mt-1 font-mono text-[9px] uppercase tracking-widest text-gray-500">Delivered Value</p></div>
                <div class="bg-[#0a0a0a] p-5"><p class="text-2xl font-black tracking-tighter text-white md:text-3xl">CIDB 7CE</p><p class="mt-1 font-mono text-[9px] uppercase tracking-widest text-gray-500">National Grading</p></div>
            </div>
        </div>
    </header>

    <section class="border-b border-gray-800 bg-[#0a0a0a] py-20 md:py-28" aria-labelledby="flagship-heading">
        <div class="mx-auto max-w-[90rem] px-6 sm:px-8 lg:px-12">
            <div class="mb-14 max-w-3xl">
                <p class="mb-3 text-[10px] font-bold uppercase tracking-widest text-unicon-green md:text-xs">Signature Works</p>
                <h2 id="flagship-heading" class="text-4xl font-extrabold uppercase leading-none tracking-tight sm:text-5xl md:text-6xl">Flagship <span class="text-unicon-green">Projects.</span></h2>
                <p class="mt-6 text-base font-light leading-relaxed text-gray-400 md:text-lg">
                    {nflag} projects that define what Unicon builds — chosen for engineering difficulty, scale, and the calibre of the clients who trusted us with them.
                </p>
            </div>
            <div class="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 md:gap-8">{''.join(flags)}
            </div>
        </div>
    </section>

    <section class="relative overflow-hidden border-b border-gray-800 bg-unicon-black py-20 md:py-24">
        <div class="absolute inset-0 opacity-10">
            <img src="{img(B,'Construction-Workers-Building-Roof-Structure-Scaffolding-UniconSA.jpg',1600)}" alt="" aria-hidden="true" class="h-full w-full object-cover grayscale">
        </div>
        <div class="relative z-10 mx-auto max-w-[90rem] px-6 sm:px-8 lg:px-12">
            <div class="mx-auto max-w-4xl border-l-2 border-unicon-green pl-6 sm:pl-10">
                <p class="mb-4 font-mono text-[10px] uppercase tracking-widest text-unicon-green">1993 // Msinga Top, KwaZulu-Natal</p>
                <h2 class="text-3xl font-extrabold uppercase leading-tight tracking-tight sm:text-4xl md:text-5xl">A school opened by <span class="text-unicon-green">Nelson Mandela.</span></h2>
                <p class="mt-6 text-base font-light leading-relaxed text-gray-400 md:text-lg">
                    Two years into trading, Unicon built the classroom blocks and hall at Mawele High School in deep rural Msinga. The completed school was officially opened by President Nelson Mandela.
                </p>
                <p class="mt-4 text-base font-light leading-relaxed text-gray-400 md:text-lg">
                    Our first years were spent on clinics, hospitals and schools for communities that had none — then on the reservoirs and water schemes that now make up the largest part of this portfolio. That order of priorities has not changed.
                </p>
                <a href="{BASE}/home/history.html" target="_top" class="mt-8 inline-flex items-center gap-2 border-b-2 border-white pb-1 text-xs font-bold uppercase tracking-widest text-white transition-colors hover:border-unicon-green hover:text-unicon-green">Read our full history <i class="fa-solid fa-arrow-right"></i></a>
            </div>
        </div>
    </section>

    <section id="database" class="scroll-mt-24 bg-[#050505] py-20 md:py-28" aria-labelledby="database-heading">
        <div class="mx-auto max-w-[90rem] px-6 sm:px-8 lg:px-12">
            <div class="mb-10 max-w-3xl">
                <p class="mb-3 text-[10px] font-bold uppercase tracking-widest text-unicon-green md:text-xs">The Full Record</p>
                <h2 id="database-heading" class="text-4xl font-extrabold uppercase leading-none tracking-tight sm:text-5xl">Master <span class="text-outline">Database.</span></h2>
                <p class="mt-6 text-base font-light leading-relaxed text-gray-400">
                    All {len(recs)} completed and in-progress projects. Filter by discipline, decade or contract scale — or search across clients, consultants, materials and scope.
                </p>
            </div>

            <div class="mb-8 rounded-sm border border-gray-800 bg-[#111111] p-5 shadow-xl sm:p-6">
                <div class="mb-5">
                    <label for="searchInput" class="sr-only">Search projects</label>
                    <div class="relative">
                        <i class="fa-solid fa-magnifying-glass pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-gray-500"></i>
                        <input type="search" id="searchInput" placeholder="Search clients, consultants, materials, scope…" autocomplete="off"
                               class="search-input w-full border border-gray-700 bg-[#050505] py-4 pl-12 pr-4 font-mono text-xs uppercase tracking-widest text-white outline-none transition-all placeholder:text-gray-600 focus:border-unicon-green">
                    </div>
                </div>
                <div class="space-y-4">
                    <div>
                        <p class="mb-2 font-mono text-[9px] uppercase tracking-widest text-gray-500">Discipline</p>
                        <div class="flex flex-wrap gap-2">
                            <button type="button" data-filter="sector" data-value="all" class="chip is-active rounded-sm border border-gray-700 px-3 py-2 text-[9px] font-bold uppercase tracking-widest text-gray-400 transition-colors hover:border-unicon-green hover:text-white">All</button>{chips("sector", SECTORS)}
                        </div>
                    </div>
                    <div>
                        <p class="mb-2 font-mono text-[9px] uppercase tracking-widest text-gray-500">Decade</p>
                        <div class="flex flex-wrap gap-2">
                            <button type="button" data-filter="decade" data-value="all" class="chip is-active rounded-sm border border-gray-700 px-3 py-2 text-[9px] font-bold uppercase tracking-widest text-gray-400 transition-colors hover:border-unicon-green hover:text-white">All</button>{chips("decade", DECADES)}
                        </div>
                    </div>
                    <div>
                        <p class="mb-2 font-mono text-[9px] uppercase tracking-widest text-gray-500">Contract scale</p>
                        <div class="flex flex-wrap gap-2">
                            <button type="button" data-filter="band" data-value="all" class="chip is-active rounded-sm border border-gray-700 px-3 py-2 text-[9px] font-bold uppercase tracking-widest text-gray-400 transition-colors hover:border-unicon-green hover:text-white">All</button>{chips("band", BANDS)}
                            <button type="button" data-filter="flagship" data-value="1" class="chip rounded-sm border border-unicon-green/40 px-3 py-2 text-[9px] font-bold uppercase tracking-widest text-unicon-green transition-colors hover:bg-unicon-green hover:text-white"><i class="fa-solid fa-star mr-1.5 text-[8px]"></i>Flagship only</button>
                        </div>
                    </div>
                </div>
                <div class="mt-5 flex items-center justify-between border-t border-gray-800 pt-4">
                    <p class="font-mono text-[10px] uppercase tracking-widest text-gray-500">Showing <span id="rowCount" class="font-bold text-white">{len(recs)}</span> of {len(recs)} projects</p>
                    <button type="button" id="resetFilters" class="font-mono text-[10px] uppercase tracking-widest text-gray-500 transition-colors hover:text-unicon-green"><i class="fa-solid fa-rotate-left mr-1"></i>Reset</button>
                </div>
            </div>

            <div id="projectGrid" class="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">{''.join(cards)}
            </div>

            <div id="noResults" class="hidden rounded-sm border border-gray-800 bg-[#111111] p-16 text-center">
                <i class="fa-solid fa-triangle-exclamation mb-4 text-4xl text-gray-600"></i>
                <p class="text-lg font-bold uppercase tracking-widest text-white">No projects match</p>
                <p class="mt-2 font-mono text-sm text-gray-500">Try a different search term or clear the filters.</p>
            </div>
        </div>
    </section>

    <section class="border-y border-gray-800 bg-[#0a0a0a] py-20" aria-labelledby="portfolio-heading">
        <div class="mx-auto max-w-[90rem] px-6 sm:px-8 lg:px-12">
            <h2 id="portfolio-heading" class="mb-3 text-3xl font-extrabold uppercase tracking-tight sm:text-4xl">Where the Work Sits</h2>
            <p class="mb-10 max-w-2xl text-base font-light text-gray-400">Bulk water and wastewater make up the core of the portfolio — the disciplines where zero-leakage tolerances leave no margin for error.</p>
            <div class="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-8">
                {''.join(f'''<div class="rounded-sm border border-gray-800 bg-[#111111] p-5 text-center">
                  <i class="fa-solid {ICON[s]} mb-3 text-xl text-unicon-green"></i>
                  <p class="text-2xl font-black tracking-tighter text-white">{sector_counts.get(s,0)}</p>
                  <p class="mt-1 font-mono text-[8px] uppercase leading-tight tracking-widest text-gray-500">{e(s)}</p>
                </div>''' for s in SECTORS)}
            </div>
            <div class="mt-10 grid grid-cols-1 gap-6 md:grid-cols-3">
                <div class="border border-gray-800 bg-[#111111] p-6">
                    <h3 class="mb-4 flex items-center gap-2 font-bold uppercase tracking-tight text-white"><i class="fa-solid fa-building text-unicon-green"></i> Repeat Clients</h3>
                    <p class="text-xs font-light leading-relaxed text-gray-400">{', '.join(f'<strong class="text-gray-200">{e(c)}</strong> ({n})' for c,n in top_clients if c!='—')} — measured by number of separate contracts awarded.</p>
                </div>
                <div class="border border-gray-800 bg-[#111111] p-6">
                    <h3 class="mb-4 flex items-center gap-2 font-bold uppercase tracking-tight text-white"><i class="fa-solid fa-file-contract text-unicon-green"></i> Contract Formats</h3>
                    <p class="text-xs font-light leading-relaxed text-gray-400">Delivered under <strong class="text-gray-200">GCC 1990, 2004, 2010 and 2015</strong>, and <strong class="text-gray-200">JBCC Series 3 through 6.2</strong> — as full contracts, construction management and turnkey appointments.</p>
                </div>
                <div class="border border-gray-800 bg-[#111111] p-6">
                    <h3 class="mb-4 flex items-center gap-2 font-bold uppercase tracking-tight text-white"><i class="fa-solid fa-layer-group text-unicon-green"></i> Applied Materials</h3>
                    <p class="text-xs font-light leading-relaxed text-gray-400">Post-tensioned concrete cables, <strong class="text-gray-200">XYPEX</strong> crystalline waterproofing, geomembrane liners, high-density rebar, slip-form concrete and structural steel portal frames.</p>
                </div>
            </div>
        </div>
    </section>

    <section class="bg-[#050505] py-20 md:py-24" aria-labelledby="gallery-heading">
        <div class="mx-auto max-w-[90rem] px-6 sm:px-8 lg:px-12">
            <div class="mb-10 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
                <div class="max-w-2xl">
                    <p class="mb-3 text-[10px] font-bold uppercase tracking-widest text-unicon-green md:text-xs">From the Sites</p>
                    <h2 id="gallery-heading" class="text-3xl font-extrabold uppercase tracking-tight sm:text-4xl">Work in Progress</h2>
                    <p class="mt-4 text-base font-light text-gray-400">Dome pours, liner installations, deck pours and mass earthworks — photographed on our own sites.</p>
                </div>
                <a href="{BASE}/projects/photo-gallery.html" target="_top" class="shrink-0 text-[10px] font-bold uppercase tracking-widest text-unicon-green transition-colors hover:text-white">Full photo gallery <i class="fa-solid fa-arrow-right ml-1"></i></a>
            </div>
            <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-8">{gal}
            </div>
            <p class="mt-6 font-mono text-[10px] uppercase tracking-widest text-gray-600">Select any frame to enlarge</p>
        </div>
    </section>

    <section class="border-t border-gray-800 bg-[#0a0a0a] py-20" aria-labelledby="archive-heading">
        <div class="mx-auto max-w-[90rem] px-6 sm:px-8 lg:px-12">
            <h2 id="archive-heading" class="mb-3 text-3xl font-extrabold uppercase tracking-tight sm:text-4xl">Browse by Decade</h2>
            <p class="mb-10 max-w-2xl text-base font-light text-gray-400">Tabulated archives for every era of the company.</p>
            <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                <a href="{BASE}/projects/2020s-&amp;-active-projects.html" target="_top" class="group rounded-sm border border-gray-800 bg-[#111111] p-8 transition-colors hover:border-unicon-green">
                    <p class="text-4xl font-black tracking-tighter text-white group-hover:text-unicon-green">2020s</p>
                    <p class="mt-2 font-mono text-[10px] uppercase tracking-widest text-gray-500">Active &amp; Current</p>
                    <p class="mt-4 text-xs font-light text-gray-400">Resort wastewater works, retail centres, fuel stations and turnkey residential.</p>
                    <span class="mt-6 inline-block text-[10px] font-bold uppercase tracking-widest text-unicon-green">Open archive <i class="fa-solid fa-arrow-right ml-1"></i></span>
                </a>
                <a href="{BASE}/projects/2010s-archive.html" target="_top" class="group rounded-sm border border-gray-800 bg-[#111111] p-8 transition-colors hover:border-unicon-green">
                    <p class="text-4xl font-black tracking-tighter text-white group-hover:text-unicon-green">2010s</p>
                    <p class="mt-2 font-mono text-[10px] uppercase tracking-widest text-gray-500">Water &amp; Bridges</p>
                    <p class="mt-4 text-xs font-light text-gray-400">Post-tensioned reservoirs, provincial bridges, canals and campuses.</p>
                    <span class="mt-6 inline-block text-[10px] font-bold uppercase tracking-widest text-unicon-green">Open archive <i class="fa-solid fa-arrow-right ml-1"></i></span>
                </a>
                <a href="{BASE}/projects/2000s-archive.html" target="_top" class="group rounded-sm border border-gray-800 bg-[#111111] p-8 transition-colors hover:border-unicon-green">
                    <p class="text-4xl font-black tracking-tighter text-white group-hover:text-unicon-green">2000s</p>
                    <p class="mt-2 font-mono text-[10px] uppercase tracking-widest text-gray-500">Commercial Scale</p>
                    <p class="mt-4 text-xs font-light text-gray-400">Shopping centres, industrial plants, abstraction works and water schemes.</p>
                    <span class="mt-6 inline-block text-[10px] font-bold uppercase tracking-widest text-unicon-green">Open archive <i class="fa-solid fa-arrow-right ml-1"></i></span>
                </a>
                <a href="{BASE}/projects/1990s-archive.html" target="_top" class="group rounded-sm border border-gray-800 bg-[#111111] p-8 transition-colors hover:border-unicon-green">
                    <p class="text-4xl font-black tracking-tighter text-white group-hover:text-unicon-green">1990s</p>
                    <p class="mt-2 font-mono text-[10px] uppercase tracking-widest text-gray-500">Foundations</p>
                    <p class="mt-4 text-xs font-light text-gray-400">Rural clinics, hospitals, schools and the first water schemes.</p>
                    <span class="mt-6 inline-block text-[10px] font-bold uppercase tracking-widest text-unicon-green">Open archive <i class="fa-solid fa-arrow-right ml-1"></i></span>
                </a>
            </div>
        </div>
    </section>

    <section class="bg-unicon-green bg-blueprint-dark py-20 text-white">
        <div class="mx-auto flex max-w-[90rem] flex-col items-center justify-between gap-8 px-6 sm:px-8 md:flex-row lg:px-12">
            <div>
                <h2 class="mb-2 text-2xl font-extrabold uppercase tracking-tight text-unicon-black sm:text-3xl">Engage Our Engineering Team</h2>
                <p class="max-w-xl text-sm font-light text-white/90">For detailed BOQs, the full project schedule with contract values, or procurement auditing, start a technical enquiry — we respond with the engineer who would run your job.</p>
            </div>
            <div class="flex w-full flex-col gap-4 sm:flex-row md:w-auto">
                <a href="{BASE}/contact.html" target="_top" class="whitespace-nowrap border border-unicon-black bg-unicon-black px-8 py-4 text-center text-xs font-bold uppercase tracking-widest text-white shadow-xl transition-all hover:bg-white hover:text-unicon-black"><i class="fa-solid fa-paper-plane mr-2"></i> Contact Us</a>
                <a href="{BASE}/home/about.html" target="_top" class="whitespace-nowrap border border-unicon-black px-8 py-4 text-center text-xs font-bold uppercase tracking-widest text-unicon-black transition-all hover:bg-unicon-black hover:text-white"><i class="fa-solid fa-building-columns mr-2"></i> Company Profile</a>
            </div>
        </div>
    </section>

{FOOTER}

    <div id="lightbox" class="fixed inset-0 z-[200] hidden items-center justify-center bg-black/95 p-4 backdrop-blur-sm" role="dialog" aria-modal="true" aria-label="Enlarged project photograph">
        <button type="button" id="lightboxClose" class="absolute right-5 top-5 p-3 text-2xl text-white transition-colors hover:text-unicon-green" aria-label="Close image viewer"><i class="fa-solid fa-xmark"></i></button>
        <figure class="max-h-full max-w-6xl text-center">
            <img id="lightboxImg" alt="" class="mx-auto max-h-[80vh] w-auto max-w-full rounded-sm object-contain">
            <figcaption id="lightboxCap" class="mt-4 font-mono text-[10px] uppercase tracking-widest text-gray-400"></figcaption>
        </figure>
    </div>

    <script>
    document.addEventListener('DOMContentLoaded', function () {{
        var y = document.getElementById('year-footer');
        if (y) y.textContent = new Date().getFullYear();

        // The nav comes from tools/chrome.py and is a slide-in drawer, so this
        // must toggle the transform the way every other page does.
        var btn = document.getElementById('mobile-menu-btn');
        var menu = document.getElementById('mobile-menu');
        if (btn && menu) {{
            btn.addEventListener('click', function () {{
                var closed = menu.classList.toggle('translate-x-full');
                btn.setAttribute('aria-expanded', String(!closed));
                var i = btn.querySelector('i');
                i.classList.toggle('fa-bars', closed);
                i.classList.toggle('fa-xmark', !closed);
            }});
        }}

        var banner = document.getElementById('cookie-banner');
        var accept = document.getElementById('accept-cookies');
        function lift() {{
            document.documentElement.style.setProperty('--fab-lift',
                banner && !banner.classList.contains('translate-y-full')
                    ? banner.offsetHeight + 16 + 'px' : '0px');
        }}
        if (banner && accept) {{
            if (!localStorage.getItem('unicon_cookie_consent')) {{
                setTimeout(function () {{ banner.classList.remove('translate-y-full'); lift(); }}, 1500);
            }}
            accept.addEventListener('click', function () {{
                localStorage.setItem('unicon_cookie_consent', 'true');
                banner.classList.add('translate-y-full');
                lift();
            }});
            window.addEventListener('resize', lift);
        }}

        var cards = Array.prototype.slice.call(document.querySelectorAll('.project-card'));
        var search = document.getElementById('searchInput');
        var count = document.getElementById('rowCount');
        var empty = document.getElementById('noResults');
        var grid = document.getElementById('projectGrid');
        var base = {{ sector: 'all', decade: 'all', band: 'all', flagship: false, q: '' }};
        var state = Object.assign({{}}, base);

        function apply() {{
            var n = 0;
            cards.forEach(function (c) {{
                var ok = (state.sector === 'all' || c.dataset.sector === state.sector) &&
                         (state.decade === 'all' || c.dataset.decade === state.decade) &&
                         (state.band === 'all' || c.dataset.band === state.band) &&
                         (!state.flagship || c.dataset.flagship === '1') &&
                         (state.q === '' || c.dataset.search.indexOf(state.q) !== -1);
                c.classList.toggle('hidden', !ok);
                if (ok) n++;
            }});
            count.textContent = n;
            empty.classList.toggle('hidden', n !== 0);
            grid.classList.toggle('hidden', n === 0);
        }}

        document.querySelectorAll('.chip').forEach(function (chip) {{
            chip.addEventListener('click', function () {{
                var type = chip.dataset.filter, val = chip.dataset.value;
                if (type === 'flagship') {{
                    state.flagship = !state.flagship;
                    chip.classList.toggle('is-active', state.flagship);
                }} else {{
                    state[type] = val;
                    document.querySelectorAll('.chip[data-filter="' + type + '"]').forEach(function (o) {{
                        o.classList.toggle('is-active', o === chip);
                    }});
                }}
                apply();
            }});
        }});

        if (search) search.addEventListener('input', function () {{ state.q = this.value.trim().toLowerCase(); apply(); }});

        var reset = document.getElementById('resetFilters');
        if (reset) reset.addEventListener('click', function () {{
            state = Object.assign({{}}, base);
            if (search) search.value = '';
            document.querySelectorAll('.chip').forEach(function (c) {{
                c.classList.toggle('is-active', c.dataset.value === 'all' && c.dataset.filter !== 'flagship');
            }});
            apply();
        }});

        var lb = document.getElementById('lightbox'),
            lbImg = document.getElementById('lightboxImg'),
            lbCap = document.getElementById('lightboxCap'),
            lastFocus = null;
        function openLb(src, cap) {{
            lastFocus = document.activeElement;
            lbImg.src = src; lbImg.alt = cap; lbCap.textContent = cap;
            lb.classList.remove('hidden'); lb.classList.add('flex');
            document.body.style.overflow = 'hidden';
            document.getElementById('lightboxClose').focus();
        }}
        function closeLb() {{
            lb.classList.add('hidden'); lb.classList.remove('flex');
            lbImg.removeAttribute('src'); document.body.style.overflow = '';
            if (lastFocus) lastFocus.focus();
        }}
        document.querySelectorAll('.gal-item').forEach(function (g) {{
            g.addEventListener('click', function () {{ openLb(g.dataset.full, g.dataset.caption); }});
        }});
        document.getElementById('lightboxClose').addEventListener('click', closeLb);
        lb.addEventListener('click', function (ev) {{ if (ev.target === lb) closeLb(); }});
        document.addEventListener('keydown', function (ev) {{
            if (ev.key === 'Escape' && !lb.classList.contains('hidden')) closeLb();
        }});
    }});
    </script>

    <!-- POPIA BANNER -->
    <div id="cookie-banner" class="fixed bottom-0 left-0 w-full bg-[#0a0a0a]/95 backdrop-blur-md border-t border-[#475c4d] z-[9999] transform translate-y-full transition-transform duration-500 flex flex-col sm:flex-row items-center justify-between p-4 sm:px-8 shadow-[0_-10px_30px_rgba(0,0,0,0.5)]">
        <div class="flex items-start gap-4 mb-4 sm:mb-0">
            <i class="fa-solid fa-cookie-bite text-[#475c4d] text-xl mt-1 hidden sm:block"></i>
            <div>
                <h4 class="text-white text-xs font-bold uppercase tracking-widest mb-1">Data & Privacy Control</h4>
                <p class="text-gray-400 text-[10px] sm:text-xs font-light leading-relaxed max-w-3xl">
                    Unicon Construction utilizes essential cookies and analytics to optimize user experience and track site performance. By proceeding, you consent to our digital privacy framework in accordance with the POPI Act.
                </p>
            </div>
        </div>
        <div class="flex gap-3 w-full sm:w-auto">
            <button id="accept-cookies" class="flex-1 sm:flex-none px-6 py-2.5 bg-[#475c4d] text-white text-[10px] font-bold uppercase tracking-widest hover:bg-white hover:text-black transition-colors whitespace-nowrap rounded-sm">
                Acknowledge & Accept
            </button>
        </div>
    </div>

    <!-- SCRIPTS -->
</body>
</html>
"""

open(os.path.join(ROOT,"projects.html"),"w",encoding="utf-8").write(HTML)
print("projects:",len(recs),"flagships:",nflag,"decades:",DECADES)
print("sectors:",dict(sector_counts))
print("verified photos:",sum(1 for r in recs if r["verified"]))
print("bytes:",len(HTML))
