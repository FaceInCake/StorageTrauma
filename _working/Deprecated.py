# type: ignore , This entire code if full of incomplete references

class Pricing (NamedTuple):
    """Contains info for getting the price of an item."""
    basePrice : int
    multiplier :defaultdict[str,float]
    
    @classmethod
    def from_Element (cls, e:Element|None) -> Self|None:
        "Expects the Price Element `e`, return None if `e` is None"
        if e is None: return None
        if e.tag != "Price" : raise ValueError(f"Expected a 'Price' element but was '{e.tag}'")
        basePriceS = e.get("baseprice", "")
        if basePriceS=="": raise KeyError("Expected a 'baseprice' attribute from Element `e`")
        basePrice :int = int(basePriceS)
        prefix = "merchant"
        pd :dict[str,float] = {
            id[len(prefix):] if id.startswith(prefix) else id
            : float(p.get("multiplier",1.0))
            for p in e.findall("Price")
            if (id := p.get("storeidentifier","")) != ""
        }
        return cls(
            basePrice= basePrice,
            multiplier= defaultdict(lambda: 1.0, pd)
        )

    def to_json (self) -> str:
        return '{"baseprice":"%s",%s}' % (
            self.basePrice,
            ','.join(
                '"%s":"%s"' % (k, v)
                for k,v in self.multiplier.items()
            )
        )

class Availability (NamedTuple):
    "Contains info for the availability for an item."
    default  : int
    avail : defaultdict[str,int]

    #TODO: <Price minleveldifficulty="50">

    @classmethod
    def from_Element (cls, e:Element|None) -> Self|None:
        "Expects the parent Price element `e`, returns None if `e` is None"
        if e is None: return None
        if e.tag != "Price" : raise ValueError(f"Expected a 'Price' element but was '{e.tag}'")
        baseSold :str = e.get("sold","")
        baseAvail = e.get("minavailable")
        pd :dict[str,int] = {
            id: 0 if p.get("sold",baseSold)=="false" else
                int(p.get("minavailable") or baseAvail or 1)
            for p in e.findall("Price")
            if (id := p.get("storeidentifier","")) != ""
        }
        return Availability(
            default=
        )
        pd2 :dict[str,int] = {
            i : 0 if notSold else int(avail)
            for i, avail, notSold in [(
                p.get("storeidentifier", ""),
                p.get("minavailable", 1),
                p.get("sold") == "false"
                ) for p in e.findall("Price")
            ] if i != ""
        }
        return Availability( # TODO: Verify how the inheritence of base availability works
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

def get_listings (e:Element|None) -> PricingInfo | None:
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

# Listing Constructor
if bp == 0: raise ValueError(f"Price element {e} either doesn't have a `baseprice` attribute when it should or it is invalid")
kargs = {}
def checkFor (attr:str, type):
    if (x := e.get(attr.lower().strip('_'))):
        kargs[attr] = type(x)
checkFor('sold', bool)
checkFor('_minAvailable', int)
checkFor('_maxAvailable', int)
checkFor('canBeSpecial', bool)
checkFor('multiplier', float)
checkFor('minDifficulty', int)
checkFor('buyingPriceModifier', float)
checkFor('requiresUnlock', bool)
if (x := e.findall('Reputation')):
    kargs['repRequired'] = {
        o.get('faction','') : int(o.get('min',0))
        for o in x
    }
return cls(bp, **kargs)