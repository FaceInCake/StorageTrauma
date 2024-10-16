"This Epic file contains a bunch of classes and functions for parsing and manipulating Barotrauma Items"

from collections import defaultdict # Dictionary with default value, good for getting price of item, as it MIGHT vary per merchant
from tkinter import filedialog, messagebox # Dialog boxes
from os import path, makedirs, remove # For creating cross-platform file URIs
from sys import platform # windows or linux or whatnot
from typing import NamedTuple,Self,Any,Literal,TypeVar,Protocol,Sequence,SupportsIndex,Final,Iterator
from contextlib import suppress
from functools import cache
from xml.etree.ElementTree import parse, Element # Turn that text into objects!
from glob import glob # Find them files
from numpy import multiply # Epic math
# from scipy.sparse import csr_matrix # Can represent a directed graph, used for con or decon trees
from cv2 import resize, imread, imwrite, IMREAD_UNCHANGED # OpenCV image editing tools, yes its a bit overkill, bite me
from cv2.typing import MatLike

_RT = TypeVar('_RT', bound=object, covariant=True) # "Generic return type"
_PT = TypeVar("_PT") # "Generic parameter type"

class SupportGet (Protocol[_RT]):
    def get (self, __key :str) -> _RT|None: return None

class Nothing:
    "Any getters return self or empty. Always falsy."
    def __getattribute__(self, __name: str) -> Self: return self
    def __call__(self, *args: Any, **kwds: Any) -> Self: return self
    def __getitem__(self, __i: SupportsIndex) -> Self: return self
    def __bool__ (self) -> Literal[False]: return False
    def __iter__ (self) -> Iterator[Any]: return iter([])

def try_get (e :SupportGet[_PT], default:_PT, keys :Sequence[str|None]) -> _PT:
    if len(keys)==0: return default
    if keys[0] is not None: 
        test = e.get(keys[0])
        if test is not None: return test
    return try_get(e, default, keys[1:])

def maybe (obj :_PT|None) -> _PT|Nothing:
    "Returns a falsy `Nothing` object if `obj` is None, effectively working as the save-navigation operator"
    return Nothing() if obj is None else obj


class ContentPackage (NamedTuple):
    """Can be 'Vanilla' or any other mod package for example,
    every content package is basically a list of URIs to xml files that contain various resources.
    `version` should be in the format: '0-20-0-0' for example. Everything else is a list of filepaths"""
    name :str
    version :str
    items :list[str]
    submarines :list[str]
    characters :list[str]
    afflictions :list[str]
    structures :list[str]
    npc_sets :list[str]
    # Theres more types but I dont care about them rn, add 'em when you want

    @classmethod
    def from_Element(cls, e:Element) -> Self:
        def get_files (type:str) -> list[str]:
            return [j for j in [i.get("file","") for i in e.findall(type)] if j!=""]
        name = e.get("name","")
        if name == "": raise ValueError("Invalid name or no name found")
        version = e.get("gameversion","").replace(".","-")
        if version == "": raise ValueError("Invalid version or no version found")
        return cls(
            name=name, version=version,
            items= get_files("Item"),
            submarines= get_files("Submarine"),
            characters=  get_files("Character"),
            afflictions= get_files("Afflictions"),
            structures= get_files("Structure"),
            npc_sets= get_files("NPCSets")
        )

class Listing:

    __slots__ = 'id', 'basePrice', 'available', 'multiplier', 'buyMod', 'maxAvail', 'minDifficulty', 'repReq'
    def __init__(self, basePrice:int, available:int, maxAvailable:int|None, multiplier:float=1.0,
                 buyingPriceModifier:float=1.0, minDifficulty:int=0, repRequired:dict[str,int]={}):
        self.basePrice :int = basePrice
        self.available :int = available
        self.multiplier :float = multiplier
        self.buyMod :float = buyingPriceModifier
        self.maxAvail :int = maxAvailable or available
        self.minDifficulty :int = minDifficulty
        self.repReq :dict[str,int] = repRequired
    
    def is_available (self, curDiff:int, rep:dict[str,int]) -> bool:
        return  self.is_not_sold() and (
                curDiff >= self.minDifficulty) and (
                all(
                    rep.get(fac,0) >= val
                    for fac,val in self.repReq.items()
                ))

    def get_price (self) -> int:
        return round(self.basePrice * self.multiplier * self.buyMod)
    
    def is_not_sold (self) -> bool:
        return self.available==0 and self.maxAvail==0
    

def get_listings (e:Element|None) -> defaultdict[str,Listing] | None:
    """Pass the parent 'Price' element to this function"""
    if e is None: return None
    if e.tag != "Price" : raise ValueError(f"Expected a 'Price' element but was '{e.tag}'")
    basePrice :int = int(e.get("baseprice", 0))
    if basePrice==0: raise KeyError("Expected a valid 'baseprice' attribute from Element `e`")
    baseSold :str = e.get("sold", "")
    baseAvail :int|None =        int(_)   if (_:= e.get("minavailable", "")).isdecimal() else None
    baseMaxAvail :int|None =     int(_)   if (_:= e.get("maxavailable", "")).isdecimal() else None
    baseMultiplier :float|None = float(_) if (_:= e.get("multiplier", "")) else None
    baseBuyMod :float|None =     float(_) if (_:= e.get("buyingpricemodifier", "")) else None
    baseDifficulty :int|None =   int(_)   if (_:= e.get("minleveldifficulty","")).isdecimal() else None
    baseRepReq :dict[str,int] = {
        fac : int(m)
        for r in e.findall("Reputation")
        if (fac := r.get("faction","")) != ""
        and (m := r.get("min","")) != ""
    }
    prefix = "merchant"
    pd :dict[str,Listing] = {
        id : Listing(basePrice,
            available= 0 if p.get("sold",baseSold)=="false" else int(p.get("minavailable","") or baseAvail or 1),
            maxAvailable= int(p.get("maxavailable","") or baseMaxAvail or 0) or None ,
            multiplier= float(p.get("multiplier","") or baseMultiplier or 1.0),
            buyingPriceModifier= float(p.get("buyingpricemodifier","") or baseBuyMod or 1.0),
            minDifficulty= int(p.get("minleveldifficulty","") or baseDifficulty or 0),
            repRequired= {
                fac : int(m)
                for r in p.findall("Reputation")
                if (fac := r.get("faction","")) != ""
                and (m := r.get("min","")) != ""
            } or baseRepReq
        )
        for p in e.findall("Price")
        if (_id := p.get("storeidentifier","")) != ""
        and (id := _id[len(prefix):] if _id.startswith(prefix) else _id)
    }
    default = Listing(basePrice,
        available= 0 if e.get("sold","")=="false" else int(baseAvail or 0),
        maxAvailable= int(baseMaxAvail or 0) or None,
        multiplier= float(baseMultiplier or 0.0) or 1.0,
        buyingPriceModifier= float(baseBuyMod or 0.0) or 1.0,
        minDifficulty= int(baseDifficulty or 0),
        repRequired= baseRepReq
    )
    return defaultdict(lambda: default, pd)

DEFAULT_TIME :Final[Literal["15.0"]] = "15.0" #TODO: Verify me
class Deconstructable (NamedTuple):
    "Stores info about what an item deconstructs into"
    output : dict[str,int]
    "The resultant items, as 'item id' -> 'count'"
    time : float
    "The base of how many seconds it takes to decon"

    @classmethod
    def from_Element (cls, e:Element|None) -> Self|None:
        "Expects Deconstruct Element `e`, returns None if `e` is None"
        if e is None: return None
        if e.tag != "Deconstruct": raise ValueError(f"Expected 'Deconstruct' Element but was '{e.tag}'")
        time = e.get("time", "")
        if time=="": raise KeyError("ASFASREFER") # TODO: me
        items = e.findall("Item")
        dd :dict[str,int] = defaultdict(lambda: 0)
        for i in items: # An item can be listed multiple times, this code makes sure they get added up
            id = i.get("identifier", "")
            if id != "": dd[id] += int(i.get("amount", 1))
        return cls(output=dict(dd), time=float(time))

    def to_json (self) -> str:
        return "{%s}" % (
            ','.join(
                f'"{k}":{v}'
                for k,v in self.output.items()
            )
        )

class Recipe (NamedTuple):
    """Helper class for `Item`. This object should be a member of the Item that this recipe results in"""
    required : dict[str,int]
    "What items are required to craft an item as 'item id' -> 'count required'"
    output : int
    "The number of items that result from this recipe"
    machine :str
    "The machine you need to use to see this recipe"
    time : float
    "Number of seconds it takes to craft with this recipe"
    skills : dict[str,int]
    "Required skills to craft with this recipe, as 'skill id' -> 'level'"

    @classmethod
    def from_Element (cls, e:Element) -> Self|None:
        "Expects a 'Fabricate' Element `e`, returns None if `e` is a vending machine recipe."
        machine = e.get("suitablefabricators", "fabricator") #TODO: Verify default is always 'fabricator'
        if machine == "vendingmachine": return None
        time = e.get("requiredtime", DEFAULT_TIME)
        return cls(
            required= {
                id : int(a)
                for id, a in [(
                    i.get("identifier", ""),
                    i.get("amount", 1)
                    ) for i in e.findall("RequiredItem")
                ] if id != ""
            },
            output= int(e.get("amount", 1)),
            machine= machine,
            time= float(time),
            skills= {
                id : int(l)
                for id, l in [(
                    i.get("identifier", ""),
                    i.get("level", "")
                    ) for i in e.findall("RequiredSkill")
                ] if id != "" and l != ""
            }
        )

    def to_json (self):
        return '{"required":{%s},"output":%d}' % (
            ",".join(f'"{r}":{self.required[r]}' for r in self.required),
            self.output
        )

Colour = tuple[float,float,float]
WHITE = (1.0, 1.0, 1.0)

class Texture (NamedTuple):
    """Stores information needed to fetch a texture image for an item.
    Used for InventoryIcon and Sprite."""
    path : str
    "The file path to the sprite sheet where the texture is in"
    rect : tuple[int,int,int,int]
    "(x,y,w,h) rectangle for where the icon is on the sprite sheet"
    colour : Colour
    "Colouring of this texture, defaults to all 1.0"

    @classmethod
    def from_Element (cls, e:Element, dir:str, colour:Colour|None=None) -> Self:
        """Finds and parses out the source rect for an InventoryIcon OR Sprite.
        `dir` should be the rel path to where the Element was found"""
        tex = e.get("texture", "")
        if tex == "": raise KeyError("Expected a 'texture' attribute but not found")
        if not tex.startswith("Content/"):
            tex = path.join(dir, tex)
        rect = e.get("sourcerect", "")
        if rect != "":
            rectList = [int(s) for s in rect.split(",", 3)]
            rect = (rectList[0], rectList[1], rectList[2], rectList[3])
        else:
            ses = e.get("sheetelementsize", "")
            si = e.get("sheetindex", "")
            if ses == "" or si == "":
                raise KeyError("No sourcerect or sheetindex and sheetelementsize found")
            w, h = tuple(int(s) for s in ses.split(",", 1))
            x, y = tuple(int(s) for s in si.split(",", 1))
            rect = (x*w, y*h, w, h)
        return cls(path=tex, rect=rect, colour=colour or WHITE)

class InventoryIcon (Texture):

    @classmethod
    def from_Element (cls, e:Element|None, dir:str, colour:Colour|None=None) -> Self|None:
        "Same as Texture.from_Element(). Expects an 'InventoryIcon' Element, it may be None in which case None is returned"
        if e is None: return None
        if e.tag != "InventoryIcon": raise ValueError(f"Expected an 'InventoryIcon' Element but was '{e.tag}'")
        return super().from_Element(e, dir, colour)

class Sprite (Texture):

    @classmethod
    def from_Element (cls, e:Element, dir:str, colour:Colour|None=None) -> Self:
        "Same as `Texture.from_Element()`, but expects a Sprite Element"
        if e is None: raise TypeError("No Element supplied")
        if e.tag.lower() != "sprite": raise ValueError(f"Expected an 'Sprite' Element but was '{e.tag}'")
        return super().from_Element(e, dir, colour)

class Item (NamedTuple):
    "Contains all important information relavent for a given item"
    id : str
    "Identifier string"
    tags : list[str]
    "Used to index groups of items, usually"
    name : str
    "Full item name for a set language"
    desc : str
    "In game description for a set language"
    category : str
    "Self explanetory, chosen by the devs. Always English?"
    listing : Listing
    "Contains info for the availability and pricing of the item"
    deconsTo : Deconstructable | None
    "What this item deconstructs into, may not exist"
    recipes : list[Recipe]
    "A list of recipes that can result in this item, may be empty"
    icon : InventoryIcon | None
    "Info for how to get the inventory icon, may not exist and instead just use the Sprite"
    sprite : Sprite
    "Info for how to get the in game sprite texture for this item"

    @classmethod
    def from_Element (cls, e:Element, texts:dict[str,str], variantOf:Element|None = None) -> Self|None:
        """Parses the given Element and constructs an Item object.
        `texts` is for i18n as 'text id' -> 'text', see fetch_language().
        Returns None if `e` is invalid, meaning a valid Item could not be created.
        If the item is a variation of another item, pass in `variantOf`."""
        # e.tag NOT guaranteed to be Item for whatever reason
        dir = e.get("dir", "")
        if dir == "": return None
        def fetch (target:str) -> Element | None:
            i = e.find(target)
            if i is None: i = e.find(target.lower())
            if i is None:
                if variantOf is None: return None
                j = variantOf.find(target)
                if j is None: j = variantOf.find(target.lower())
                return j
            if variantOf is not None:
                j = variantOf.find(target)
                if j is None: j = variantOf.find(target.lower())
                if j is not None:
                    if not i:
                        i.extend(iter(j)) # Update i with j's children if i doesnt have any
                    ik = i.keys()
                    for jk, ji in j.items():
                        if jk not in ik:
                            i.set(jk, ji) # Set attribute from variantOf if parent doesnt have it
            return i
        # end func
        e_sprite = fetch("Sprite")
        if e_sprite is None: return None
        id :str = e.get("identifier") or e.get("file","")+f"_{hash(e)}"
        name :str = texts.get(f"entityname.{e.get('nameidentifier', id)}", id)
        desc :str = texts.get(f"entitydescription.{e.get('descriptionidentifier', id)}", "") #or texts.get(f"entitydescription.{id}", "")
        def backup_get (target:str, default:str)->str:
            return e.get(target.lower()) or e.get(target) or maybe(variantOf).get(target.lower()) or maybe(variantOf).get(target) or default
        cat :str = backup_get("Category", "None")
        with suppress(AttributeError): # Handle Genetic Material genericism
            name, desc = (lambda g: (
                (lambda t: name.replace("[type]", t)) ( #type: ignore
                    (lambda i: texts.get(i)) #type: ignore
                    (g.get("nameidentifier"))), #type: ignore
                (lambda v0,v1: desc.replace("[value]", f"{v0}-{v1}"))
                (g.get("tooltipvaluemin"), g.get("tooltipvaluemax")) #type: ignore
            ))(fetch("GeneticMaterial"))
        e_t :str = backup_get("Tags", "")
        e_p :Element|None = fetch("Price")
        e_f :list[Element] = e.findall("Fabricate") or maybe(variantOf).findall("Fabricate") or []
        def parse_colour (key:str) -> Colour|None:
            valueStr = backup_get(key, "")
            if valueStr=="": return None
            valueList = [
                float(s) if '.' in s else int(s)/255.0
                for s in valueStr.split(",",3)
            ]
            return (valueList[0], valueList[1], valueList[2])
        _ic :Colour|None = parse_colour("InventoryIconColor")
        _sc :Colour|None = parse_colour("SpriteColor")
        return cls(
            id=id, name=name, desc=desc, category=cat,
            tags= [s.strip() for s in e_t.split(",")],
            listing=get_listings(e_p),
            deconsTo= Deconstructable.from_Element(fetch("Deconstruct")),
            recipes= [r for r in (Recipe.from_Element(f) for f in e_f) if r is not None],
            icon= InventoryIcon.from_Element(fetch("InventoryIcon"), dir, _ic),
            sprite= Sprite.from_Element(e_sprite, dir, _sc)
        )

    def to_json (self) -> str:
        return '{"id":"%s","name":"%s","category":"%s","desc":"%s","tags":[%s],"prices":%s,"available":%s,"deconsTo":%s,"recipes":[%s]}' % (
            self.id, self.name, self.category,
            self.desc.replace('"', '\\"'),
            ",".join(f'"{s}"' for s in self.tags),
            self.price.to_json() if self.price is not None else "{}",
            self.available.to_json() if self.available is not None else "{}",
            self.deconsTo.to_json() if self.deconsTo is not None else "{}",
            ",".join(r.to_json() for r in self.recipes)
        )


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
        for npcset in parse(rootDir + url).getroot()
        for npc in npcset.findall("npc")
        if npc.get("campaigninteractiontype")=="Store"
        and (id := npc.get("identifier","")) != ""
        and id != "merchanttutorial"
    ]

def fetch_xml_elements (rootDir:str, URLs :list[str]) -> dict[str, Element]:
    """Parses all given xml resources for their contained elements.
    Also attaches the folder it was in, relative to Barotrauma, and attaches the file NAME."""
    allElms :dict[str, Element] = {}
    filePathList :list[str] = [path.join(rootDir,p).replace('\\','/') for p in URLs]
    for filePath in filePathList:
        tree :Element = parse(filePath).getroot()
        dir, file = filePath.rsplit("/", 1)
        dir = path.relpath(dir, rootDir)
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
    return textDict
        
def fetch_items (xmlItems :dict[str,Element], texts :dict[str,str]) -> dict[str,Item]:
    items0 :list[Item|None] = [
        Item.from_Element(e, texts, try_get(xmlItems, None, (e.get("variantof"),)))
        for e in xmlItems.values()        
    ]
    items :dict[str,Item] = { i.id : i for i in items0 if i is not None}
    print("Parsed out %4d Items" % len(items))
    return items

def filter_items (items :dict[str,Item]) -> dict[str,Item]:
    "Modifies `items`, returns the filtered out items!"
    rest :dict[str,Item] = {}
    for id, i in list(items.items()):
        if i.price is None and len(i.recipes)==0 and i.deconsTo is None:
            rest[id] = items.pop(id)
    print("Filtered out %3d Items, %4d remaining" % (
        len(rest), len(items)
    ))
    return rest


def export_items_to_json (items :dict[str,Item], targetDir:str):
    if not path.isdir(targetDir): makedirs(targetDir)
    with open(targetDir+"/!ItemList.json", 'w') as fout:
        fout.write('['+','.join(f'"{i}"' for i in items.keys())+']')
    for id, item in items.items():
        name :str = targetDir+'/'+id+".json"
        with open(name, 'w') as fout:
            fout.write(item.to_json())

class ImageDownloader:
    "Construct me with the rootDir in order to call `download_` `sprites`/`icons`"
    ICON_SIZE :Final[Literal[64]] = 64

    def __init__(self, rootDir:str) -> None:
        self.__rootDir = rootDir

    @cache
    def __get_img (self, filePath:str) -> MatLike:
        "Fetches the given sprite sheet, also caches it for re-use"
        return imread(path.join(self.__rootDir, filePath), IMREAD_UNCHANGED)

    def __prepare_folder (self, dir:str):
        "Makes and clears the given directory path"
        makedirs(dir, exist_ok=True)
        all(remove(p) for p in glob(f"{dir}/*.png")) # should only be PNGs
    
    def __get_resize (self, i:Texture) -> tuple[int,int]:
        """Calculates the new smaller size while maintaining aspect ratio"""
        S = ImageDownloader.ICON_SIZE # shorthand
        w, h = tuple(i.rect[2:4])
        return (S, round(S*h/w)) if w > h else (round(S*w/h), S)

    @staticmethod
    def __crop (img: MatLike, rect:tuple[int,int,int,int]) -> MatLike:
        """Crops the given opencv `img` using the given xywh `rect`, returns the result"""
        return img[rect[1]:rect[1]+rect[3], rect[0]:rect[0]+rect[2]]

    @staticmethod
    def __colour_image (img: MatLike, colour:Colour) -> MatLike:
        if colour != WHITE:
            c = list(colour)
            c.reverse() # RGB -> BGR
            return multiply(img[:,:], [*c, 1.0])
        return img

    def download_sprites (self, items:dict[str,Item], targetDir:str) -> bool:
        "Attempts to download the sprites for the given `items`, looking in `self.rootDir`, exporting to `targetDir`"
        self.__prepare_folder(targetDir)
        return all(
            imwrite(
                f"{targetDir}/{id}.png",
                self.__colour_image(
                    self.__crop(
                        self.__get_img(item.sprite.path),
                        item.sprite.rect),
                    item.sprite.colour)
            ) for id, item in items.items()
        )    

    def download_icons (self, items:dict[str,Item], targetDir:str) -> bool:
        "Attempts to download the icons for the given `items`, same as download_icons, but backs up to resized sprites if needed"
        self.__prepare_folder(targetDir)
        return all(
            imwrite(
                f"{targetDir}/{id}.png",
                self.__colour_image(
                    resize(
                        self.__crop(
                            self.__get_img(item.icon.path),
                            item.icon.rect),
                        self.__get_resize(item.icon)),
                    item.icon.colour),
            ) if item.icon is not None else
            imwrite(
                f"{targetDir}/{id}.png",
                self.__colour_image(
                    resize(
                        self.__crop(
                            self.__get_img(item.sprite.path),
                            item.sprite.rect),
                        self.__get_resize(item.sprite)),
                    item.sprite.colour)
            ) for id, item in items.items()
        )
# end ImageDownloader

def export_items_to_searchDoc (items:dict[str,Item], targetPath:str):
    "`others` is any filtered out items from `items`, as they may still be referenced to"
    makedirs(path.dirname(targetPath), exist_ok=True)
    with open(targetPath, 'w') as fout: fout.write(
        "[%s]" % (
            ",".join(
                '{"id":"%s","name":"%s","category":"%s","desc":"%s","tags":"%s","price":"%s","deconsTo":"%s","recipes":"%s"}' % (
                    id, item.name, item.category,
                    item.desc.replace('"', '\\"'),
                    ",".join(item.tags),
                    str(maybe(item.price).basePrice or ""),
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

    # export_items_to_json(items, f"assets/json/items/{package.version}")
    # export_items_to_searchDoc(items, f"assets/json/items/{package.version}/!SearchDoc.json")
    
    # imgdl = ImageDownloader(rootDir)
    # imgdl.download_sprites(items, f"assets/images/items/{package.version}/sprites")
    # imgdl.download_icons(items, f"assets/images/items/{package.version}/icons")
    # del imgdl

    print("Done!")
    return 0

if __name__=="__main__": exit(main())
