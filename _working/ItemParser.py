"This Epic file contains a bunch of classes and functions for parsing and manipulating Barotrauma Items"

from collections import defaultdict # Dictionary with default value, good for getting price of item, as it MIGHT vary per merchant
from tkinter import filedialog, messagebox # Dialog boxes
from os import path, makedirs # For creating cross-platform file URIs
from sys import platform # windows or linux or whatnot
from typing import NamedTuple,Self,Any,Literal,TypeVar,Protocol,Sequence,SupportsIndex,Final,Iterator
from contextlib import suppress
from xml.etree.ElementTree import parse, Element # Turn that text into objects!
from json import load as load_json
from glob import glob # Find them files
# from scipy.sparse import csr_matrix # Can represent a directed graph, used for con or decon trees


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
    `version` should be in the format '0-20-0-0', for example. Everything else is a list of filepaths"""
    name :str
    version :str
    items :list[str]
    submarines :list[str]
    characters :list[str]
    afflictions :list[str]
    structures :list[str]
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
            structures= get_files("Structure")
        )

class Pricing (NamedTuple):
    """Contains info for getting the price of an item.
    The `basePrice` is what it is, everything else is after the multiplier.
    For example, `military` might have a price multiplier of 1.1, which is multiplied with the `basePrice`.  
    You might need to do rounding where necessary."""
    basePrice : int
    outpost  : float
    city     : float
    mine     : float
    military : float
    research : float
    engineering : float
    medical  : float
    armory   : float

    @classmethod
    def from_Element (cls, e:Element|None) -> Self|None:
        "Expects the Price element `e`, returns None if `e` is None"
        if e is None: return None
        if e.tag != "Price" : raise ValueError(f"Expected a 'Price' element but was '{e.tag}'")
        basePrice = e.get("baseprice", "")
        if basePrice=="": raise KeyError("Expected a 'baseprice' attribute from Element `e`")
        basePrice = int(basePrice)
        pd :dict[str,float] = {
            i : float(m) * basePrice
            for i,m in [(
                p.get("storeidentifier", ""),
                p.get("multiplier", 1.0)
                ) for p in e.findall("Price")
            ] if i != ""
        }
        return cls(
            basePrice= basePrice,
            outpost=  pd.get("merchantoutpost", basePrice),
            city=     pd.get("merchantcity", basePrice),
            mine=     pd.get("merchantmine", basePrice),
            military= pd.get("merchantmilitary", basePrice),
            research= pd.get("merchantresearch", basePrice),
            engineering= pd.get("merchantengineering", basePrice),
            medical=  pd.get("merchantmedical", basePrice),
            armory=   pd.get("merchantarmory", basePrice),
        )

    def to_json (self) -> str:
        return '{"default":%d,"outpost":%f,"city":%f,"mine":%f,"military":%f,"research":%f,"engineering":%f,"medical":%f,"armory":%f}' % (
            self.basePrice, self.outpost, self.city, self.mine, self.military, self.research, self.engineering, self.medical, self.armory )

class Availability (NamedTuple):
    "Contains info for the availability for an item."
    default  : int
    outpost  : int
    city     : int
    mine     : int
    military : int
    research : int
    engineering : int
    medical  : int
    armory   : int

    @classmethod
    def from_Element (cls, e:Element|None) -> Self|None:
        "Expects the parent Price element `e`, returns None if `e` is None"
        if e is None: return None
        if e.tag != "Price" : raise ValueError(f"Expected a 'Price' element but was '{e.tag}'")
        baseAvail = 0 if e.get("sold")=="false" else int(e.get("minavaiable", 1))
        pd :dict[str,int] = {
            i : 0 if notSold else int(avail)
            for i, avail, notSold in [(
                p.get("storeidentifier", ""),
                p.get("minavailable", 1),
                p.get("sold") == "false"
                ) for p in e.findall("Price")
            ] if i != ""
        }
        return cls( # TODO: Verify how the inheritence of base availability works
            default= baseAvail,
            outpost= pd.get("merchantoutpost", 0),
            city= pd.get("merchantcity", 0),
            mine= pd.get("merchantmine", 0),
            military= pd.get("merchantmilitary", 0),
            research= pd.get("merchantresearch", 0),
            engineering= pd.get("merchantengineering", 0),
            medical= pd.get("merchantmedical", 0),
            armory= pd.get("merchantarmory", 0)
        )

    def to_json (self) -> str:
        return '{"default":%d,"outpost":%d,"city":%d,"mine":%d,"military":%d,"research":%d,"engineering":%d,"medical":%d,"armory":%d}' % (
            self.default, self.outpost, self.city, self.mine, self.military, self.research, self.engineering, self.medical, self.armory )

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
        if time=="": raise KeyError("ASFASREFER")
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
            vals = tuple(int(s) for s in rect.split(",", 3))
            rect = (vals[0], vals[1], vals[2], vals[3])
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
    price : Pricing | None
    "Contains the item price for each merchant"
    available : Availability | None
    "Contains the number of items for sail for each merchant"
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
        dir = e.get("dir", "") # dir is supplied by me, used for sprites/icons
        if dir == "": return None
        def fetch (target:str) -> Element|None:
            i = e.find(target)
            if i is None: i = e.find(target.lower())
            if i is None:
                if variantOf is None: return None
                j = variantOf.find(target)
                if j is None: j = variantOf.find(target.lower())
                if j is None: return None
                j.set('__dir', variantOf.get('dir',''))
                return j
            if variantOf is not None:
                j = variantOf.find(target)
                if j is None: j = variantOf.find(target.lower())
                if j is not None:
                    if not len(i):
                        i.extend(iter(j)) # Update i with j's children if i doesnt have any
                    ik = i.keys()
                    for jk, ji in j.items():
                        if jk not in ik:
                            i.set(jk, ji) # Set attribute from variantOf if parent doesnt have it
            return i
        # end func
        e_sprite = fetch("Sprite")
        e_icon = fetch("InventoryIcon")
        if e_sprite is None: return None
        id :str = e.get("identifier") or e.get("file","")+f"_{hash(e)}"
        name :str = texts.get(f"entityname.{e.get('nameidentifier', id)}", id)
        desc :str = texts.get(f"entitydescription.{e.get('descriptionidentifier', id)}", "") #or texts.get(f"entitydescription.{id}", "")
        def backup_get (target:str, default:str)->str:
            return e.get(target.lower()) or e.get(target) or maybe(variantOf).get(target.lower()) or maybe(variantOf).get(target) or default
        cat :str = backup_get("Category", "None")
        with suppress(AttributeError): # Handle Genetic Material genericism, I decided to use functional programming here becuase I can and its fun
            name, desc = (lambda g: (
                (lambda t: name.replace("[type]", t)) (
                    (lambda i: texts.get(i,""))
                    (g.get("nameidentifier",""))),
                (lambda v0,v1: desc.replace("[value]", f"{v0}-{v1}"))
                (g.get("tooltipvaluemin"), g.get("tooltipvaluemax"))
            ))(fetch("GeneticMaterial"))
        e_t :str = backup_get("Tags", "")
        e_p :Element|None = fetch("Price")
        e_f :list[Element] = e.findall("Fabricate") or maybe(variantOf).findall("Fabricate") or []
        def parse_colour (key:str) -> Colour|None:
            valueS = backup_get(key, "")
            if valueS=="": return None
            nums = [
                float(s) if '.' in s else int(s)/255.0
                for s in valueS.split(",",3)
            ]
            return (nums[0], nums[1], nums[2])
        _ic :Colour|None = parse_colour("InventoryIconColor")
        _sc :Colour|None = parse_colour("SpriteColor")
        return cls(
            id=id, name=name, desc=desc, category=cat,
            tags= [s.strip() for s in e_t.split(",")],
            price= Pricing.from_Element(e_p),
            available= Availability.from_Element(e_p),
            deconsTo= Deconstructable.from_Element(fetch("Deconstruct")),
            recipes= [r for r in (Recipe.from_Element(f) for f in e_f) if r is not None],
            icon= InventoryIcon.from_Element(e_icon, maybe(e_icon).get('__dir') or dir, _ic),
            sprite= Sprite.from_Element(e_sprite, e_sprite.get('__dir') or dir, _sc)
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
            "~/snap/steam/common/.local/share/"+steamGame,
            "/home/faceincake/snap/steam/common/.steam/steam/steamapps/common/Barotrauma"
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

def fetch_xml_elements (rootDir:str, URIs :list[str]) -> dict[str, Element]:
    """Parses all given xml resources for their contained elements.
    Also attaches the folder it was in, relative to Barotrauma, and attaches the file NAME."""
    allElms :dict[str, Element] = {}
    filePathList :list[str] = [path.join(rootDir,p).replace('\\','/') for p in URIs]
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

def refetch_items (folderPath:str) -> dict[str,Item]:
    retr :dict[str,Item] = {}
    for path in glob(folderPath+"/*.json"):
        with open(path) as fin:
            o = load_json(fin)
            p = o['prices']
            if p:
                p['basePrice'] = p['default']
                del p['default']
            retr[o['id']] = Item(
                o['id'], o['tags'], o['name'], o['desc'], o['category'],
                Pricing(**p) if p else None,
                Availability(**o['available']) if o['available'] else None,
                Deconstructable(o['deconsTo'], 30) if o['deconsTo'] else None,
                [Recipe(r['required'], r['output'], "Undefined", 30, {}) for r in o['recipes']],
                None,
                Sprite("No", (0,0,0,0), (0,0,0))
            )
    return retr

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


def export_items_to_json (items:dict[str,Item], targetDir:str):
    makedirs(targetDir+'/items', exist_ok=True)
    with open(targetDir+"/ItemList.json", 'w') as fout:
        fout.write('['+','.join(f'"{i}"' for i in items.keys())+']')
    for id, item in items.items():
        name :str = targetDir+'/items/'+id+".json"
        with open(name, 'w') as fout:
            fout.write(item.to_json())


def export_items_to_searchDoc (items:dict[str,Item], targetPath:str):
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


def export_items_to_viewlist (items:dict[str,Item], targetPath:str):
    lines :list[str] = []
    for item in items.values():
        craftable = 1 if len(item.recipes) > 0 else 0
        deconable = 1 if item.deconsTo is not None else 0
        rep = f'["{item.id}","{item.name}",{maybe(item.price).basePrice or "\"\""},{craftable},{deconable}]'
        lines.append(rep)
    with open(targetPath, 'w') as fout:
        fout.write(f'[{",".join(lines)}]')


def main ():
    rootDir = fetch_barotrauma_path()
    if rootDir is None: raise IOError("Failed to find where Barotrauma is")
    print("Baro :", rootDir)
    package = fetch_content_package(rootDir, "Vanilla")
    print("Version :", package.version)
    xmlItems = fetch_xml_elements(rootDir, package.items)
    texts = fetch_language(rootDir, "English")
    items = fetch_items(xmlItems, texts)
    filter_items(items)

    # items = refetch_items(f"assets/json/1-0-7-0/items")

    # export_items_to_json(items, f"assets/json/{package.version}")
    # export_items_to_searchDoc(items, f"assets/json/{package.version}/SearchDoc.json")
    # export_items_to_viewlist(items, f"assets/json/{package.version}/ViewItemsList.json")
    
    from ItemImageDownloader import ImageDownloader
    imgdl = ImageDownloader(rootDir)
    imgdl.download_sprites(items, f"assets/images/items/{package.version}/sprites")
    imgdl.download_icons(items, f"assets/images/items/{package.version}/icons")
    del imgdl

    print("Done!")
    exit(0)

if __name__=="__main__": main()