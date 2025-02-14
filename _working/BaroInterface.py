
from typing import NamedTuple, Required, Self, TypedDict, Final, Literal, TypeVar, Any, Iterator
from collections import defaultdict
from os.path import join as path_join
from xml.etree.ElementTree import Element

_PT = TypeVar("_PT")
"Generic parameter type"

class Nothing:
    "Any getters return self or empty. Always falsy."
    def __getattribute__(self, __name: str) -> Self: return self
    def __call__(self, *args: Any, **kwds: Any) -> Self: return self
    def __getitem__(self, __i: Any) -> Self: return self
    def __bool__ (self) -> Literal[False]: return False
    def __iter__ (self) -> Iterator[Any]: return iter([])

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


# <Clear/>
# price can be alone
# <Price basePrice sold canbespecial /> (ex: flamerunique, cheaper fabrication items (can sell, cannot buy))

class Listing (TypedDict, total=False):
    "contains pricing information for single source of purchase, (a merchant). See `PricingInfo`"
    basePrice : int
    minAvailable : int
    "Should be provided. If not provided, sold should be False. 0 technically works though too, sold overrides this"
    maxAvailable : int|None
    "Defaults to minAvailable, which will be represented by None"
    sold : bool
    "Merchants can offer it"
    canBeSpecial : bool
    "Can the item be on sale, basically"
    multiplier : float
    "Different merchants have different multiplers for the basePrice"
    minLevelDifficulty : int
    "The minimum difficulty percentage point for this item to be offered"
    repRequired : dict[str, int]
    "[merchant:str] -> reputationPoints, minimum reputation needed to buy this item from this merchant"
    buyingPriceModifier : float
    "Additional price multiplier that is only applied to the purchasing of the item, not selling"
    # displaynonempty : bool # used for oxygentanks and stuff that have/show a durability
    requiresUnlock : bool
    "Some unique items require a skill point or event unlock to be to actually buy/sell that item"

class DefaultListing (Listing, total=True):
    "Copy of `Listing` but all keys are required. Used internally"
    basePrice : int
    minAvailable : int
    maxAvailable : int|None
    sold : bool
    canBeSpecial : bool
    multiplier : float
    minLevelDifficulty : int
    repRequired : dict[str, int]
    buyingPriceModifier : float
    # displaynonempty : bool # used for oxygentanks and stuff that have/show a durability
    requiresUnlock : bool
DEFAULT_LISTING = DefaultListing(
    basePrice= 0,
    minAvailable= 0,
    maxAvailable= 0,
    sold= False,
    canBeSpecial= True,
    multiplier= 1.0,
    minLevelDifficulty= 0,
    repRequired= {},
    buyingPriceModifier= 1.0,
    requiresUnlock= False
)
LISTED_DEFAULT_LISTING = DefaultListing(
    basePrice= 0,
    minAvailable= 5,
    maxAvailable= None,
    sold= True,
    canBeSpecial= True,
    multiplier= 1.0,
    minLevelDifficulty= 0,
    repRequired= {},
    buyingPriceModifier= 1.0,
    requiresUnlock= False
)

def Element_to_Listing (e:Element) -> Listing:
    def parse_str (obj:str) -> int|float|bool|str:
        if obj.lower() == 'true': return True
        if obj.lower() == 'false': return False
        if obj.isnumeric(): return int(obj)
        x,y,z = obj.partition('.')
        if y != '' and x.isnumeric() and z.isnumeric():
            return float(obj)
        return obj
    kwargs :dict[str,Any] = {
        k : parse_str(x)
        for k in DEFAULT_LISTING.keys()
        if (x := e.get(k.lower()))
    }
    if (x := e.findall('Reputation')):
        kwargs['repRequired'] = {
            o.get('faction','') : int(o.get('min',0))
            for o in x
        }
    return Listing(**kwargs)

PricingInfo = defaultdict[str, Listing]
"[MerchantName:str] -> Listing"

def Element_to_PricingInfo (parent:Element|None) -> PricingInfo | None:
    if parent is None: return None
    if parent.tag != "Price" : raise ValueError(f"Expected a 'Price' element but was '{parent.tag}'")
    default = Element_to_Listing(parent)
    rf = parent.get('requiredfaction')
    req = Element('Reputation', {'faction': r, 'min': '20'}) if (r := parent.get('requiredfaction')) else None
    pinfo :defaultdict[str, Listing] = defaultdict(lambda: default)
    for p in parent.findall('Price'):
        if (id := p.get('storeidentifier','')):
            if req is not None: p.append(req)
            pinfo[id.removeprefix('merchant')] = Element_to_Listing(p)
    # TODO: a `<Clear/>` within a price tag... wth do we do?
    return pinfo

def get_price_from_PricingInfo (p:PricingInfo, merchant:str="default") -> float:
    m = p[merchant]
    d = maybe(p.default_factory)() or {}
    basePrice = m.get("basePrice") or d.get('basePrice') or DEFAULT_LISTING["basePrice"]
    mult = m.get('multiplier') or d.get('multiplier') or DEFAULT_LISTING['multiplier']
    buyMult = m.get('buyingPriceModifier') or d.get('buyingPriceModifier') or DEFAULT_LISTING['buyingPriceModifier']
    return basePrice * mult * buyMult

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
    requiredMoney : int

    @classmethod
    def from_Element (cls, e:Element) -> Self|None:
        "Expects a 'Fabricate' Element `e`, returns None if `e` is a vending machine recipe."
        machine = e.get("suitablefabricators", "fabricator") #TODO: Verify default is always 'fabricator'
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
            },
            requiredMoney= int(e.get('requiredmoney', 0))
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
            tex = path_join(dir, tex)
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
    priceInfo : PricingInfo | None
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
        # e.tag NOT guaranteed to be Item for whatever reason, see Medical folder
        dir = e.get("dir", "") # dir is supplied by me, used for sprites/icons
        if dir == "": return None
        def fetch (target:str) -> Element | None:
            i = l[-1] if (l := e.findall(target)) else None # catch for weird edge case of duplicate tags, take last
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
        name :str = texts.get(f"entityname.{e.get('nameidentifier', id)}", [id])[0]
        desc :str = texts.get(f"entitydescription.{e.get('descriptionidentifier', id)}", [""])[0] #or texts.get(f"entitydescription.{id}", "")
        def backup_get (target:str, default:str)->str:
            return e.get(target.lower()) or e.get(target) or maybe(variantOf).get(target.lower()) or maybe(variantOf).get(target) or default
        cat :str = backup_get("Category", "None")
        # with suppress(AttributeError): # Handle Genetic Material genericism
        name, desc = (lambda g: (
            (lambda t: name.replace("[type]", t)) (
                (lambda i: texts.get(i,[''])[0])
                (g.get("nameidentifier",''))),
            (lambda v0,v1: desc.replace("[value]", f"{v0}-{v1}"))
            (g.get("tooltipvaluemin",''), g.get("tooltipvaluemax",''))
        ))(fetch("GeneticMaterial") or {})
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
            priceInfo=Element_to_PricingInfo(e_p),
            deconsTo= Deconstructable.from_Element(fetch("Deconstruct")),
            recipes= [r for r in [Recipe.from_Element(f) for f in e_f] if r is not None],
            icon= InventoryIcon.from_Element(e_icon, maybe(e_icon).get('__dir') or dir, _ic),
            sprite= Sprite.from_Element(e_sprite, e_sprite.get('__dir') or dir, _sc)
        )
