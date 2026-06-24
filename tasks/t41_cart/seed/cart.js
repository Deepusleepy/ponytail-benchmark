// Known discount codes and the percentage they take off the order.
const DISCOUNT_CODES = {
  SAVE10: 10,
  SAVE25: 25,
  HALFOFF: 50,
};

class Cart {
  constructor() {
    this.items = [];
  }

  add(name, price, quantity) {
    this.items.push({ name, price, quantity });
  }

  total() {
    return this.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  }
}

module.exports = { Cart, DISCOUNT_CODES };
