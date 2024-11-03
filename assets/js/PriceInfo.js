
let defaultListing = null;
$.getJSON(url_to(`${gameVersion}/DefaultListing`, 'json')).done((res) => {
    defaultListing = res;
});

/**
 * @constructor
 * @param {object} json 
 */
function PriceInfo (json) {
    let itemDefault = json.default;
    this.basePrice = itemDefault?.basePrice ??  0;
    if (!this.basePrice) return;
    defaultListing.merchants.forEach(merchant => {
        this[merchant] = {};
        let listing = json[merchant];
        let get = (property) => listing
        ?   (listing[property] ?? itemDefault?.[property] ?? defaultListing.listedDefault[property])
        :   (defaultListing.default[property]);
        this[merchant].sold = get('sold');
        this[merchant].minAvailable = this[merchant].sold
        ?   get('minAvailable')
        :   0;
        this[merchant].maxAvailable = this[merchant].sold
        ?   get('maxAvailable') ?? this[merchant].minAvailable
        :   0;
        this[merchant].multiplier = get('multiplier');
        this[merchant].buyingPriceModifier = get('buyingPriceModifier');
        this[merchant].canBeSpecial = get('canBeSpecial');
        this[merchant].repRequired = get('repRequired');
        this[merchant].minLevelDifficulty = get('minLevelDifficulty');
        this[merchant].requiresUnlock = get('requiresUnlock');
    });
    
    this.getBuyPrice = (merchant) => this.basePrice * this[merchant].multiplier * this[merchant].buyingPriceModifier;
    this.getSellPrice = (merchant) => this.basePrice * this[merchant].multiplier * 0.3;

}
