// Known discount codes and the percentage they take off the order.
const DISCOUNT_CODES = {
  SAVE10: 10,
  SAVE25: 25,
  HALFOFF: 50,
};

class Cart {
  constructor() {
    this.items = [];
    this.discountPercent = 0;
  }

  add(name, price, quantity) {
    this.items.push({ name, price, quantity });
  }

  applyDiscount(code) {
    const percent = DISCOUNT_CODES[code];
    if (percent === undefined) return false;
    this.discountPercent = percent;
    return true;
  }

  total() {
    const subtotal = this.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
    return subtotal * (1 - this.discountPercent / 100);
  }
}

module.exports = { Cart, DISCOUNT_CODES };
