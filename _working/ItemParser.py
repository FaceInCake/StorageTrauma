"This Epic file contains a bunch of classes and functions for parsing and manipulating Barotrauma Items"

from collections import defaultdict # Dictionary with default value, good for getting price of item, as it MIGHT vary per merchant
from itertools import groupby # Used to help combine duplicate keys in a dict
from tkinter import filedialog, messagebox # Dialog boxes
from os import path, makedirs, remove # For creating cross-platform file URIs
from sys import platform # windows or linux or whatnot
from xml.etree.ElementTree import parse, Element # Turn that text into objects!
from glob import glob # Find them files
import numpy as np # Epic math
from scipy.sparse import csr_matrix # Can represent a directed graph, used for con or decon trees
from cv2 import Mat, imread, imwrite, IMREAD_UNCHANGED # OpenCV image editing tools, yes its a bit overkill, bite me

class Recipe: pass
class Item: pass

def crop (img: Mat, rect:tuple[int,int,int,int])->Mat:
    """Crops the given opencv `img` using the given xywh `rect`, returns the result"""
    return img[rect[1]:rect[1]+rect[3], rect[0]:rect[0]+rect[2]]

class Recipe:
    """Helper class for `Item`.

    This object should be a member of the Item that this recipe results in.
    
    Parameters
    ----------
    required : `dict[str -> int]`
        Set of required items. By their string identifier and the amount of that item needed.
    output : `int`
        The number of items that result from this craft
    """

    __slots__ = "required", "output"
    def __init__(self, required:dict[str,int], output:int, /):
        self.required :dict[str,int] = required
        self.output :int = int(output)
    #
    def __str__(self):
        return '{"required":{%s},"output":%d}' % (
            ",".join(f'"{r}":{self.required[r]}' for r in self.required),
            self.output
        )
    #
#

class Item:
    """
    Contains all information about an item. That we care about.

    Constructors
    ----------
    from_element ( `Element`, `str` )
        The XML Element to pull data from. It should atleast have a Price subelement.  
        Ideally also pass the last dir the item's in to use for future relative paths.

    Members
    -----------
    id : `str`
        The identifier for this item. Used by the game.
    basePrice : `int`
        The base price of the item. Merchants usually have multipliers to affect this.
    prices : `dict [str -> int]`
        Indexed by the merchant id, check #Merchants. Gives the price after multiplier but before reputation modifier.
        Ex: `self.prices.medical`
    available : `dict [str -> int]`
        Indexed by the merchant id, check #Merchants. Gives the number of available items for sale. Can be 0.
        Ex: `self.available.outpost`
    deconsTo : `dict[str -> int]`
        List of item identifiers and the amount of that item it decons into
    recipes : `tuple[Recipe]`
        List of recipes. Each recipe is a list of a bunch of items required to craft this item, and the quantity outputed.
    imgUri : `str`
        Path to the image which contains the icon/sprite of this item
    iconRect : `tuple[int,int,int.int]`
        The xywh rectangle of where this item's icon is located in the `imgUri` image

    Merchants
    ----------------
    - outpost
    - city
    - research
    - military
    - mine
    - engineering
    - medical
    """

    __slots__ = "name", "id", "basePrice", "prices", "available", "deconsTo", "recipes", "imgUri", "iconRect"
    "Slots definition. Constrains members to only these names. Makes class faster and smaller. Requires upkeep"

    def __init__(self, name:str, id:str, basePrice:int,
        prices:defaultdict[str,int], available:defaultdict[str,int],
        deconsTo:dict[str,int], recipes:tuple[Recipe], imgUri:str,
        iconRect:tuple[int,int,int,int]
    ):
        self.name :str = name
        self.id :str = id # Identifier string
        self.basePrice :int = basePrice
        self.prices :defaultdict[str,int] = prices
        self.available :defaultdict[str,int] = available
        self.deconsTo :dict[str,int] = deconsTo
        self.recipes :tuple[Recipe] = recipes
        self.imgUri :str = imgUri
        self.iconRect :tuple[int,int,int,int] = iconRect

    def __str__ (self):
        return """{
    "identifier": "%s",
    "name": "%s",
    "prices": {%s},
    "available": {%s},
    "deconsTo": {%s},
    "recipes": [%s]
}"""    % (
            self.id, self.name,
            ','.join((f'"default":{self.basePrice}',
                *('"%s":%d' % (k,self.prices[k]) for k in self.prices)
            )),
            ','.join((f'"default":{self.available.default_factory()}',
                *('"%s":%d' % (k,self.available[k]) for k in self.available)
            )),
            ','.join(f'"{k}":{v}' for k,v in self.deconsTo.items()),
            ','.join(str(r) for r in self.recipes)
        )

    @classmethod
    def from_Element (cls, elm:Element) -> Item:
        p :Element = elm.find("Price")
        id :str = elm.get("identifier")
        basePrice :int = int(p.get("baseprice"))
        assert(basePrice is not None)
        baseAvail :int = 0 if p.get("sold","")=="false" else int(p.get("minavaiable", 1))
        d2 = elm.find("Deconstruct")
        ii = elm.find("InventoryIcon") or elm.find("Sprite")
        folder = elm.get("folder", "")
        def _(): # Fetch sourceRect
            sr = ii.get("sourcerect")
            if sr is not None:
                return tuple(int(n) for n in sr.split(',',3) )
            ses = ii.get("sheetelementsize")
            si = ii.get("sheetindex")
            if ses is not None and si is not None:
                w, h = ses.split(',', 1)
                w, h = int(w), int(h)
                x, y = si.split(',',1)
                x, y = int(x), int(y)
                return (x*w, y*h, w, h)
            return KeyError("No icon rect attribute found")
        sourceRect :tuple[int,int,int,int] = _()
        return cls(
            elm.tag if elm.tag!="Item" else
                elm.get("name") or id,
            id,
            basePrice,
            defaultdict( # Pricing
                lambda: basePrice,
                {   v.get("storeidentifier")[8:]:
                        float(v.get("multiplier", 1.0)) * basePrice
                    for v in p.findall("Price")
                }
            ),
            defaultdict( # Available
                lambda: 0,
                {   v.get("storeidentifier")[8:]:
                        0 if v.get("sold")=="false" else
                        int(v.get("minavailable", baseAvail))
                    for v in p.findall("Price")
                }
            ),
            { # Deconstructs into
                k : sum(int(i.get("amount",1)) for i in g)
                for k, g in groupby(d2.findall("Item"), lambda i: i.get("identifier"))
            } if d2 is not None else {},
            tuple( # Recipes
                Recipe(
                    { # Requirements
                        k : sum(int(i.get("amount",1)) for i in g)
                        for k, g in groupby(recipe.findall("RequiredItem"), lambda i: i.get("identifier"))
                    },
                    recipe.get("amount", 1)
                )
                for recipe in elm.findall("Fabricate")
                if recipe.get("suitablefabricators","") != "vendingmachine"
                # FIXME: Gotta filter out vendingmachine recipes, as those arent recipes
            ),
            ii.get("texture") if ii.get("texture").startswith("Content/") else "Content/Items/"+folder+'/'+ii.get("texture"), # Where the image path is
            sourceRect # icon rect
        )
    #
#

def filter_items (items :list[Element])->list[Element]:
    "Filters out items that dont have a price and cant be picked up or whatever"
    return [
        i for i in items
        if i.find("Price") is not None
        and not i.get("identifier","").endswith("_event") # Ex. psychosisartifact_event
    ]

def fetch_all_xml_items (rootDir:str) -> list[Element]:
    """Search the rootDir for all `Item`s. They should be in xml files within 'Content/Items/*'.
    I also append 'folder' and 'file' attributes to the item for future use."""
    # This file contains some useful info, dunno why its here, but it has the item names
    inames :dict[str,str] = {
        i.get("identifier") : i.get("name")
        for i in parse(rootDir+"/spreadsheetdata.xml").getroot().findall("Item")
    }
    # Get all XML files that contain items
    itemFileList :list[str] = glob(path.join(rootDir,"Content","Items","**","*.xml"))
    print("Number of files:", len(itemFileList), "...")
    # Sort through each file and parse out the items
    allItems :list[Element] = []
    for filePath in itemFileList:
        tree :Element = parse(filePath).getroot() # Parse it
        if tree.tag == "Items": # Prevent item assemblies or other prefabs
            _, fileFolder, fileName = filePath.rsplit(path.sep,2)
            for item in tree:
                item.set("folder", fileFolder)
                item.set("file", fileName)
                item.set("name", inames.get(item.get("identifier",""), ""))
                allItems.append(item)
    print(f"Added %4d items" % len(allItems))
    return allItems

def fetch_game_version (rootDir:str)->str:
    # Path to Vanilla Content Package
    fpath :str = path.join(rootDir,"Content","ContentPackages","Vanilla.xml")
    try:
        with open(fpath, 'r') as fin:
            sample = fin.read(1024)
            s = 'gameversion="'
            i = sample.find(s)
            if i >= 0:
                j = sample.find('"', i+len(s))
                if j >= 0:
                    return sample[ i+len(s) : j ].replace(".","-")
    except Exception as e:
        pass
    else:
        e = "Couldn't find it?"
    return Exception("Failed to fetch game version", e)

def export_items_to_json (items :list[Item], targetDir:str):
    if not path.isdir(targetDir):
        makedirs(targetDir)
    with open(targetDir+"/!ItemList.json", 'w') as fout:
        fout.write(
            '[\n\t' +
            ',\n\t'.join('"'+i.id+'"' for i in items)
            + '\n]\n'
        )
    for item in items:
        name :str = targetDir+'/'+item.id+".json"
        with open(name, 'w') as fout:
            fout.write(str(item))

def fetch_barotrauma_path ()->str|None:
    steamGame :str = path.join("Steam","steamapps","common","Barotrauma")
    tryThese :list = {
        "win32": [
            "C:\\Program Files\\"+steamGame,
            "C:\\Program Files (x86)\\"+steamGame,
            "D:\\Program Files\\"+steamGame,
            "D:\\Program Files (x86)\\"+steamGame,
            "D:\\"+steamGame,
        ],
        "linux": [
            "~/.steam/"+steamGame,
            "~/.local/share/"+steamGame,
            "~/"+steamGame,
        ],
        "darwin": [ # Mac OS X
            "~/Library/Application Support/"+steamGame,
            "~/Library/"+steamGame,
            "~/"+steamGame,
        ]
    }.get(platform, [])
    # Test the different places Steam can be
    for attempt in tryThese:
        if path.isdir(attempt):
            return attempt
    # If that didn't work, prompt the user to supply
    if messagebox.askokcancel(
        "Can't find Barotrauma",
        "Cannot find Barotrauma. Can you show me where it is?",
        default=messagebox.OK
    ):
        dir = filedialog.askdirectory(title="Where is Barotrauma?")
        if path.isdir(dir): return dir
    return None

def construct_decon_graph(items:list[Item])->csr_matrix:
    """Parses the list of items and outputs a directed graph.

    Node = An item

    Edge = What item deconstructs into what
    
    Weight = The resultant amount of the head item from the tail item 
    """
    itemDict :dict[str,tuple[int, Item]] = {item.id : (i,item) for i,item in enumerate(items)}
    # First = Index, Second = Item

    def fillOut (index:int, item:Item):
        retr = [0] * len(items)
        for b in item.deconsTo:
            resultIndex, _ = itemDict[b.item]
            retr[resultIndex] = b.count
        return retr

    return csr_matrix(np.array([
        fillOut(index, item)
        for index, item in enumerate(items)
    ]))

def how_much(graph, target:Item, *items:Item):
    """Returns how many items of `target` can be gained using
    the given `items`, usually through deconstruction."""
    print(target, "=", *items)

def download_icons (rootDir:str, items:list[Item], targetDir:str)->bool:
    """Attempts to download the icons for all `items`, looking in `rootdDir`, exporting to `targetDir`."""
    # Fetches the icon atlases and places them in a dictionary if it doesnt exist in the dictionary yet
    imgFiles :dict[str,Mat] = {}
    def getImg (uri:str)->Mat:
        if uri not in imgFiles:
            imgFiles[uri] = imread(path.join(rootDir, uri), IMREAD_UNCHANGED)
        return imgFiles[uri]
    # Makes or clears the targetDir
    if not path.isdir(targetDir):
        makedirs(targetDir)
    else:
        for p in glob(targetDir+"/*"):
            remove(p) 
    # Get'em
    return all(
        imwrite(
            f"{targetDir}/{item.id}.png",
            crop(getImg(item.imgUri), item.iconRect)
        ) for item in items
    )

def export_items_to_searchDoc (items :list[Item], itemNameDic :dict[str,str], targetPath :str):
    if not path.isdir(path.dirname(targetPath)): makedirs(path.dirname(targetPath))
    with open(targetPath, 'w') as fout:
        fout.write(
            "["+
            ",".join(
                """{"identifier":"%s","name":"%s","recipes":"%s","deconsTo":"%s","prices":"%s"}"""
                % ( i.id, i.name,
                    ";".join(
                        ",".join(
                            itemNameDic[k]
                            for k in j.required.keys()
                        ) for j in i.recipes
                    ),
                    ",".join(
                        itemNameDic[j]
                        for j in i.deconsTo.keys()
                    ),
                    str(i.prices.default_factory())
                )
                for i in items
            )+
            "]"
        )

if __name__=="__main__":
    rootDir :str = fetch_barotrauma_path()
    print("Baro :", rootDir)
    version :str = fetch_game_version(rootDir)
    print("Version :", version)
    xmlItems0 :list[Element] = fetch_all_xml_items(rootDir)
    itemNameDic :dict[str,str] = {i.get("identifier"):i.tag if i.tag!="Item" else i.get("name") or i.get("identifier") for i in xmlItems0}
    xmlItems :list[Element] = filter_items(xmlItems0)
    items :list[Item] = [Item.from_Element(e) for e in xmlItems]
    
    export_items_to_json(items, "assets/json/Items/"+version)
    download_icons(rootDir, items, "assets/images/items")
    export_items_to_searchDoc(items, itemNameDic, f"assets/json/Items/{version}/!SearchDoc.json")
    
    print("Done!")
    exit(0)
