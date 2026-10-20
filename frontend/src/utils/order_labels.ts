// Readable labels for a drink's sugar, ice, and toppings, for any page that shows order details

const ICE_LABELS: Record<string, string> = {
    no_ice: "No ice",
    less_ice: "Less ice",
    regular_ice: "Regular ice",
    extra_ice: "Extra ice",
};

// A topping on an order item, as the orders API returns it
export type OrderItemTopping = {
    prepared_item_name: string;
    quantity: string;
};

// "50" becomes "50% sugar"
export function formatSugar(sugarLevel: string) {
    return `${sugarLevel}% sugar`;
}

// "no_ice" becomes "No ice"
export function formatIce(iceLevel: string) {
    return ICE_LABELS[iceLevel] ?? iceLevel;
}

// Each topping as "+1 Tapioca Pearls"
export function formatToppings(toppings: OrderItemTopping[]) {
    return toppings.map(
        (topping) => `+${Number(topping.quantity)} ${topping.prepared_item_name}`
    );
}
