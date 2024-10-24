
from functools import singledispatch
from typing import Any
from collections import defaultdict
from BaroInterface import maybe, Deconstructable, Recipe, Item, Listing, PricingInfo, Sprite

@singledispatch
def to_json (obj:Any) -> str:
    raise NotImplementedError(f"Type '{type(obj)}' not supported for `to_json`")

@to_json.register
def __none (obj:None) -> str:
    return 'null'

@to_json.register
def __str (obj:str) -> str:
    return '"' + obj + '"'

@to_json.register
def __number (obj:int|float) -> str:
    return str(obj)

@to_json.register
def __bool (obj:bool) -> str:
    return str(obj).lower()

@to_json.register
def __dict (obj:dict) -> str:
    return '{' + ",".join([
        f"{to_json(k)}:{to_json(v)}"
        for k,v in obj.items()
    ]) + '}'

@to_json.register
def __pricinginfo (obj:defaultdict) -> str:
    dic = dict(obj)
    dic['default'] = maybe(obj.default_factory)() or {}
    return to_json(dic)

@to_json.register
def __deconstructable (obj:Deconstructable) -> str:
    return "{%s}" % (
        ','.join(
            f'"{k}":{v}'
            for k,v in obj.output.items()
        )
    )

@to_json.register
def __recipe (obj:Recipe) -> str:
    return '{"required":{%s},"output":%d}' % (
        ",".join(f'"{r}":{obj.required[r]}' for r in obj.required),
        obj.output
    )

@to_json.register
def __item (obj:Item) -> str:
    return '{"id":"%s","name":"%s","category":"%s","desc":"%s","tags":[%s],"priceInfo":%s,"deconsTo":%s,"recipes":[%s]}' % (
        obj.id, obj.name, obj.category,
        obj.desc.replace('"', '\\"'),
        ",".join(f'"{s}"' for s in obj.tags),
        to_json(obj.priceInfo) if obj.priceInfo else r"{}",
        to_json(obj.deconsTo) if obj.deconsTo is not None else r"{}",
        ",".join(to_json(r) for r in obj.recipes)
    )

def test_main ():
    test1 = {
        'apple': 123_000,
        'BANAN123': 'thingy',
        '_ dasd': True
    }
    test2 = Listing(
        basePrice= 123,
        minAvailable= 2,
        maxAvailable= 4,
        canBeSpecial= False,
        repRequired={
            'outpost': 20
        }
    )
    test3 = PricingInfo(lambda: test2)
    test3['city'] = Listing(
        basePrice= 169,
        minAvailable=1,
        maxAvailable=None,
        minLevelDifficulty=20
    )
    test4 = Item(
        'idtag', ['misc', 'fuck'], 'ID Tag', 'this is a desc', 'Category',
        None, None, [], None, Sprite('path', (1,2,3,4), (255,200,155))
    )
    assert '__dict' in str(to_json.dispatch(type(test1))), 'Error: dictionary object not dispatching to __dict() when it should'
    assert '__dict' in str(to_json.dispatch(type(test2))), 'Error: Listing object not dispatching to __dict() when it should'
    assert '__pricinginfo' in str(to_json.dispatch(type(test3))), 'Error: PricingInfo object not dispatching to __pricinginfo() when it should'
    assert '__item' in str(to_json.dispatch(type(test4))), 'Error: Item object not dispatching to __item() when it should'
    assert to_json(True) == 'true'
    assert to_json(False) == 'false'
    assert to_json(1.23) == '1.23'
    assert to_json(15_000_000) == '15000000'
    assert to_json('thingy') == '"thingy"'
    print(to_json(test3))

if __name__ == "__main__": test_main()
