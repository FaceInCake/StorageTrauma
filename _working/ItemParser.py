"This Epic file contains a bunch of classes and functions for parsing and manipulating Barotrauma Items"

from os import makedirs
from os.path import join as path_join, isdir, relpath, dirname
from sys import platform
from glob import glob
from json import load as json_load
from tkinter import filedialog, messagebox
from xml.etree.ElementTree import parse, Element
# from scipy.sparse import csr_matrix # Can represent a directed graph, used for con or decon trees
from BaroInterface import (
    maybe, ContentPackage, Deconstructable, Item, PricingInfo, Recipe, Sprite,
    DEFAULT_LISTING, LISTED_DEFAULT_LISTING, get_price_from_PricingInfo
)
from ToJson import to_json


def fetch_barotrauma_path ()->str|None:
    steamGame :str = "Steam/steamapps/common/Barotrauma"
    tryThese :list = {
        "win32": [
            "C:/Program Files/"+steamGame,
            "C:/Program Files (x86)/"+steamGame,
            "D:/Program Files/"+steamGame,
            "D:/Program Files (x86)/"+steamGame,
            "D:/"+steamGame,
        ],
        "linux": [
            "~/.steam/"+steamGame,
            "~/.local/share/"+steamGame,
            "~/"+steamGame,
            "~/snap/steam/common/.local/share/"+steamGame,
        ],
        "darwin": [ # Mac OS X
            "~/Library/Application Support/"+steamGame,
            "~/Library/"+steamGame,
            "~/"+steamGame,
        ]
    }.get(platform, [])
    # Test the different places Steam can be
    for attempt in tryThese:
        if isdir(attempt):
            return attempt
    # If that didn't work, prompt the user to supply
    if messagebox.askokcancel(
        "Can't find Barotrauma",
        "Cannot find Barotrauma. Can you show me where it is?",
        default=messagebox.OK
    ):
        dir = filedialog.askdirectory(title="Where is Barotrauma?")
        if isdir(dir): return dir
    return None

def fetch_content_package(rootDir:str, name:str)->ContentPackage:
    """An example for `name` is 'Vanilla."""
    fpath :str = rootDir+"/Content/ContentPackages/"+name+".xml"
    tree :Element = parse(fpath).getroot()
    return ContentPackage.from_Element(tree)

def fetch_merchants (rootDir:str, URLs:list[str])->list[str]:
    "Fetches the different types of merchants, `URLs` should be the contentPackage.npc_sets"
    prefix = "merchant"
    return [
        id[len(prefix):] if id.startswith(prefix) else id
        for url in URLs
        for npcset in parse(path_join(rootDir, url)).getroot()
        for npc in npcset.findall("npc")
        if npc.get("campaigninteractiontype")=="Store"
        and (id := npc.get("identifier","")) != ""
        and id != "merchanttutorial"
    ]

def fetch_xml_elements (rootDir:str, URLs :list[str]) -> dict[str, Element]:
    """Parses all given xml resources for their contained elements.
    Also attaches the folder it was in, relative to Barotrauma, and attaches the file NAME."""
    allElms :dict[str, Element] = {}
    filePathList :list[str] = [path_join(rootDir,p).replace('\\','/') for p in URLs]
    for filePath in filePathList:
        tree :Element = parse(filePath).getroot()
        dir, file = filePath.rsplit("/", 1)
        dir = relpath(dir, rootDir)
        file = file.rsplit(".",1)[0]
        for elm in tree:
            elm.set("dir", dir)
            elm.set("file", file)
            id = elm.get("identifier","")
            if id!="": allElms[id] = elm
    print("Parsed out %4d elements" % len(allElms))
    return allElms

def fetch_language (rootDir:str, langName:str) -> dict[str,str]:
    "Returns a dictionary of 'text id' -> 'text' for the given language name"
    files = glob(rootDir+"/Content/Texts/"+langName+"/*.xml")
    textDict :dict[str,str] = {}
    for filePath in files:
        textDict.update({
            str(branch.tag) : str(branch.text)
            for branch in parse(filePath).getroot()
        })
    print("Parsed out %5d text resources" % len(textDict))
    return dict(textDict) # remove default functionality
        
def fetch_items (xmlItems :dict[str,Element], texts :dict[str,str]) -> dict[str,Item]:
    items0 :list[Item|None] = [
        Item.from_Element(e, texts, xmlItems.get(e.get("variantof",''), None))
        for e in xmlItems.values()
    ]
    items :dict[str,Item] = { i.id : i for i in items0 if i is not None}
    print("Parsed out %4d Items" % len(items))
    return items

def refetch_partial_items (folderPath:str) -> dict[str,Item]:
    retr :dict[str,Item] = {}
    for path in glob(folderPath+"/*.json"):
        with open(path) as fin:
            o = json_load(fin)
            p = o['prices']
            if p:
                p['basePrice'] = p['default']
                del p['default']
            retr[o['id']] = Item(
                o['id'], o['tags'], o['name'], o['desc'], o['category'],
                PricingInfo(**p) if p else None,
                Deconstructable(o['deconsTo'], 30) if o['deconsTo'] else None,
                [Recipe(**r) for r in o['recipes']],
                None,
                Sprite("No", (0,0,0,0), (0,0,0))
            )
    return retr

def filter_items (items :dict[str,Item]) -> dict[str,Item]:
    "Modifies `items`, returns the filtered out items!"
    rest :dict[str,Item] = {}
    for id, i in list(items.items()):
        if i.priceInfo is None and len(i.recipes)==0 and i.deconsTo is None:
            rest[id] = items.pop(id)
    print("Filtered out %3d Items, %4d remaining" % (
        len(rest), len(items)
    ))
    return rest

def export_items_to_json (items :dict[str,Item], targetDir:str):
    makedirs(targetDir+'/items', exist_ok=True)
    with open(targetDir+"/ItemList.json", 'w') as fout:
        fout.write('['+','.join(f'"{i}"' for i in items.keys())+']')
    for id, item in items.items():
        name :str = f"{targetDir}/items/{id}.json"
        with open(name, 'w') as fout:
            fout.write(to_json(item))

def export_items_to_searchDoc (items:dict[str,Item], targetPath:str):
    "`others` is any filtered out items from `items`, as they may still be referenced to"
    makedirs(dirname(targetPath), exist_ok=True)
    with open(targetPath, 'w') as fout: fout.write(
        "[%s]" % (
            ",".join(
                '{"id":"%s","name":"%s","category":"%s","desc":"%s","tags":"%s","price":"%s","deconsTo":"%s","recipes":"%s"}' % (
                    id, item.name, item.category,
                    item.desc.replace('"', '\\"'),
                    ",".join(item.tags),
                    get_price_from_PricingInfo(item.priceInfo) if item.priceInfo else 0,
                    ",".join(
                        items[i].name
                        for i in (maybe(item.deconsTo).output.keys() or list[str]())
                    ),
                    ";".join(
                        ",".join(
                            items[i].name
                            for i in r.required.keys()
                        ) for r in item.recipes
                    )
                ) for id, item in items.items()
            )
        )
    )

def export_items_to_viewlist (items:dict[str,Item], targetPath:str):
    lines :list[str] = []
    for item in items.values():
        craftable = 1 if len(item.recipes) > 0 else 0
        deconable = 1 if item.deconsTo is not None else 0
        bp = maybe(item.priceInfo)['default'].get('basePrice') or "\"\""
        rep = f'["{item.id}","{item.name}",{bp},{craftable},{deconable}]'
        lines.append(rep)
    with open(targetPath, 'w') as fout:
        fout.write(f'[{",".join(lines)}]')

def export_default_price_info (targetPath:str, merchants:list[str]):
    global DEFAULT_LISTING
    makedirs(dirname(targetPath), exist_ok=True)
    with open(targetPath, 'w') as fout:
        merchStr = ",".join([to_json(m) for m in merchants])
        defStr = to_json(DEFAULT_LISTING)
        LdefStr = to_json(LISTED_DEFAULT_LISTING)
        fout.write(f'{{"merchants":[{merchStr}],"default":{defStr},"listedDefault":{LdefStr}}}')

def export_texts_to_json (texts:dict[str,list[str]], targetFilePath:str):
    makedirs(dirname(targetFilePath), exist_ok=True)
    with open(targetFilePath, 'w', encoding='utf-8') as fout:
        fout.write(f"{{{','.join(
            f"\"{k}\":[{','.join(
                f'"{i.replace('"', '\\"')}"'
                for i in v
            )}]"
            for k,v in texts.items()
        )}}}")



def main ():
    rootDir = fetch_barotrauma_path()
    if rootDir is None: raise IOError("Failed to find where Barotrauma is")
    print("Baro :", rootDir)
    package = fetch_content_package(rootDir, "Vanilla")
    print("Version :", package.version)
    merchants = fetch_merchants(rootDir, package.npc_sets)
    xmlItems = fetch_xml_elements(rootDir, package.items)
    texts = fetch_language(rootDir, "English")
    items = fetch_items(xmlItems, texts)
    filter_items(items)

    # items = refetch_partial_items(f"assets/json/{package.version}/items")

    export_items_to_json(items, f"assets/json/{package.version}")
    export_default_price_info(f"assets/json/{package.version}/DefaultListing.json", merchants)
    export_items_to_searchDoc(items, f"assets/json/{package.version}/SearchDoc.json")
    export_items_to_viewlist(items, f"assets/json/{package.version}/ViewItemsList.json")

    # from ItemImageDownloader import ImageDownloader
    # imgdl = ImageDownloader(rootDir)
    # imgdl.download_sprites(items, f"assets/images/items/{package.version}/sprites")
    # imgdl.download_icons(items, f"assets/images/items/{package.version}/icons")
    # del imgdl

    print("Done!")
    return 0

if __name__=="__main__": exit(main())
