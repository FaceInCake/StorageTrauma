
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
