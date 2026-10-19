import { useEffect, useState } from "react";
import { apiFetch } from "../api/client";


{/* An ingredient as the Menu page sends and receives it; the three times are in minutes */}
type Ingredient = {
    id: number;
    name: string;
    base_unit: "ml" | "g" | "oz";
    default_batch_quantity: string;
    quantity_per_serving: string;
    preparation_time: number;
    cooling_time: number;
    default_shelf_life: number;
    requires_cooling: boolean;
    is_topping: boolean;
    is_active: boolean;
};


type RecipeRow = {
    prepared_item_id: number | null;
    quantity: string;
};


type Drink = {
    id: number;
    name: string;
    is_active: boolean;
    recipe: RecipeRow[];
};


{/* Form fields are kept as text while typing */}
type IngredientForm = {
    name: string;
    base_unit: Ingredient["base_unit"];
    default_batch_quantity: string;
    quantity_per_serving: string;
    preparation_time: string;
    cooling_time: string;
    default_shelf_life: string;
    requires_cooling: boolean;
    is_topping: boolean;
    is_active: boolean;
};


type DrinkForm = {
    name: string;
    is_active: boolean;
    recipe: RecipeRow[];
};


const emptyIngredientForm: IngredientForm = {
    name: "",
    base_unit: "ml",
    default_batch_quantity: "",
    quantity_per_serving: "",
    preparation_time: "",
    cooling_time: "",
    default_shelf_life: "",
    requires_cooling: false,
    is_topping: false,
    is_active: true,
};


const emptyDrinkForm: DrinkForm = {
    name: "",
    is_active: true,
    recipe: [{ prepared_item_id: null, quantity: "" }],
};


const inputStyle = "w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300";
const labelStyle = "mb-2 block text-sm font-medium text-stone-600";


{/* Find the first error message in a DRF response, even inside nested recipe rows */}
function getErrorMessage(data: unknown): string | null {
    if (typeof data === "string") {
        return data;
    }

    if (Array.isArray(data)) {
        for (const value of data) {
            const message = getErrorMessage(value);

            if (message) {
                return message;
            }
        }

        return null;
    }

    if (data && typeof data === "object") {
        return getErrorMessage(Object.values(data));
    }

    return null;
}


{/* Show minutes as minutes, hours, or days, whichever reads best */}
function formatMinutes(minutes: number) {
    if (minutes >= 1440 && minutes % 1440 === 0) {
        const days = minutes / 1440;
        return `${days} day${days === 1 ? "" : "s"}`;
    }

    if (minutes >= 60 && minutes % 60 === 0) {
        const hours = minutes / 60;
        return `${hours} hr`;
    }

    return `${minutes} min`;
}


{/* An on/off switch drawn as a status pill */}
function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (checked: boolean) => void }) {
    return (
        <button
            type="button"
            onClick={() => onChange(!checked)}
            className="flex items-center justify-between rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700"
        >
            <span>{label}</span>

            <span className={`rounded-full px-3 py-1 text-xs font-semibold ${checked ? "bg-green-100 text-green-700" : "bg-stone-100 text-stone-600"}`}>
                {checked ? "On" : "Off"}
            </span>
        </button>
    );
}


function Menu() {
    const [ingredients, setIngredients] = useState<Ingredient[]>([]);
    const [drinks, setDrinks] = useState<Drink[]>([]);

    const [ingredientForm, setIngredientForm] = useState<IngredientForm>(emptyIngredientForm);
    const [editingIngredientId, setEditingIngredientId] = useState<number | null>(null);
    const [ingredientMessage, setIngredientMessage] = useState("");

    const [drinkForm, setDrinkForm] = useState<DrinkForm>(emptyDrinkForm);
    const [editingDrinkId, setEditingDrinkId] = useState<number | null>(null);
    const [drinkMessage, setDrinkMessage] = useState("");

    const [isSaving, setIsSaving] = useState(false);


    async function getIngredients() {
        const response = await apiFetch(
            "/api/menu/ingredients/"
        );

        setIngredients(await response.json());
    }


    async function getDrinks() {
        const response = await apiFetch(
            "/api/menu/drinks/"
        );

        setDrinks(await response.json());
    }


    useEffect(() => {
        async function loadMenu() {
            await Promise.all([getIngredients(), getDrinks()]);
        }

        loadMenu();
    }, []);


    {/* Send JSON to the API, and return the error message if it was rejected */}
    async function sendJson(url: string, method: string, body: object): Promise<string | null> {
        try {
            const response = await apiFetch(
                url,
                {
                    method,

                    headers: {
                        "Content-Type": "application/json",
                    },

                    body: JSON.stringify(body),
                }
            );

            if (response.ok) {
                return null;
            }

            const data = await response.json();

            return getErrorMessage(data) || "That couldn't be saved.";
        } catch (error) {
            console.error(error);
            return "Something went wrong while saving.";
        }
    }


    function getIngredientName(ingredientId: number | null) {
        return ingredients.find((item) => item.id === ingredientId)?.name ?? "Unknown ingredient";
    }


    function getIngredientUnit(ingredientId: number | null) {
        return ingredients.find((item) => item.id === ingredientId)?.base_unit ?? "";
    }


    {/* Fill the ingredient form with an existing ingredient to edit it */}
    function editIngredient(ingredient: Ingredient) {
        setEditingIngredientId(ingredient.id);
        setIngredientMessage("");

        setIngredientForm({
            name: ingredient.name,
            base_unit: ingredient.base_unit,
            default_batch_quantity: String(Number(ingredient.default_batch_quantity)),
            quantity_per_serving: String(Number(ingredient.quantity_per_serving)),
            preparation_time: String(ingredient.preparation_time),
            cooling_time: String(ingredient.cooling_time),
            default_shelf_life: String(ingredient.default_shelf_life),
            requires_cooling: ingredient.requires_cooling,
            is_topping: ingredient.is_topping,
            is_active: ingredient.is_active,
        });
    }


    function resetIngredientForm() {
        setEditingIngredientId(null);
        setIngredientForm(emptyIngredientForm);
        setIngredientMessage("");
    }


    async function saveIngredient() {
        setIsSaving(true);

        const error = await sendJson(
            editingIngredientId === null
                ? "/api/menu/ingredients/"
                : `/api/menu/ingredients/${editingIngredientId}/`,
            editingIngredientId === null ? "POST" : "PUT",
            {
                ...ingredientForm,
                // Cooling minutes only matter when the item needs cooling
                cooling_time: ingredientForm.requires_cooling ? ingredientForm.cooling_time || "0" : "0",
            }
        );

        setIsSaving(false);

        if (error) {
            setIngredientMessage(error);
            return;
        }

        resetIngredientForm();
        setIngredientMessage(editingIngredientId === null ? "Ingredient added!" : "Ingredient saved!");

        await getIngredients();
    }


    {/* Turn an ingredient on or off right from the list */}
    async function toggleIngredient(ingredient: Ingredient) {
        const error = await sendJson(
            `/api/menu/ingredients/${ingredient.id}/`,
            "PATCH",
            { is_active: !ingredient.is_active }
        );

        if (error) {
            setIngredientMessage(error);
            return;
        }

        await getIngredients();
    }


    {/* Fill the drink form with an existing drink to edit it */}
    function editDrink(drink: Drink) {
        setEditingDrinkId(drink.id);
        setDrinkMessage("");

        setDrinkForm({
            name: drink.name,
            is_active: drink.is_active,
            recipe: drink.recipe.map((row) => ({
                prepared_item_id: row.prepared_item_id,
                quantity: String(Number(row.quantity)),
            })),
        });
    }


    function resetDrinkForm() {
        setEditingDrinkId(null);
        setDrinkForm(emptyDrinkForm);
        setDrinkMessage("");
    }


    {/* Change one recipe row; picking an ingredient fills in its serving size */}
    function updateRecipeRow(index: number, changes: Partial<RecipeRow>) {
        setDrinkForm((form) => ({
            ...form,
            recipe: form.recipe.map((row, rowIndex) => {
                if (rowIndex !== index) {
                    return row;
                }

                const updated = { ...row, ...changes };

                if (changes.prepared_item_id !== undefined) {
                    const ingredient = ingredients.find((item) => item.id === changes.prepared_item_id);
                    updated.quantity = ingredient ? String(Number(ingredient.quantity_per_serving)) : "";
                }

                return updated;
            }),
        }));
    }


    function addRecipeRow() {
        setDrinkForm((form) => ({
            ...form,
            recipe: [...form.recipe, { prepared_item_id: null, quantity: "" }],
        }));
    }


    function removeRecipeRow(index: number) {
        setDrinkForm((form) => ({
            ...form,
            recipe: form.recipe.filter((_, rowIndex) => rowIndex !== index),
        }));
    }


    async function saveDrink() {
        if (drinkForm.recipe.some((row) => row.prepared_item_id === null)) {
            setDrinkMessage("Pick an ingredient for every recipe row.");
            return;
        }

        setIsSaving(true);

        const error = await sendJson(
            editingDrinkId === null
                ? "/api/menu/drinks/"
                : `/api/menu/drinks/${editingDrinkId}/`,
            editingDrinkId === null ? "POST" : "PUT",
            drinkForm
        );

        setIsSaving(false);

        if (error) {
            setDrinkMessage(error);
            return;
        }

        resetDrinkForm();
        setDrinkMessage(editingDrinkId === null ? "Drink added!" : "Drink saved!");

        await getDrinks();
    }


    {/* Turn a drink on or off right from the list */}
    async function toggleDrink(drink: Drink) {
        const error = await sendJson(
            `/api/menu/drinks/${drink.id}/`,
            "PATCH",
            { is_active: !drink.is_active }
        );

        if (error) {
            setDrinkMessage(error);
            return;
        }

        await getDrinks();
    }


    {/* Hidden ingredients can't go in new recipes, but stay listed if a drink already uses them */}
    function getRecipeOptions(row: RecipeRow) {
        return ingredients.filter(
            (item) =>
                item.is_active ||
                item.id === row.prepared_item_id
        );
    }


    return (
        <div className="w-full px-8 py-8">

            <div className="mb-10 text-center">
                <p className="mb-2 text-4xl font-semibold text-pink-300">
                    Menu
                </p>

                <h1 className="text-2xl font-bold tracking-tight text-stone-800">
                    What does your shop make?
                </h1>

                <p className="mt-3 text-base text-stone-500">
                    Set up the ingredients you prepare in batches and the
                    drinks customers can order.
                </p>
            </div>


            {/* Ingredients */}

            <div className="mb-8 grid gap-6 xl:grid-cols-[1fr_2fr]">

                <section className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">

                    <div className="mb-6">
                        <h2 className="text-lg font-semibold text-stone-800">
                            {editingIngredientId === null ? "Add an ingredient" : "Edit ingredient"}
                        </h2>

                        <p className="mt-1 text-sm text-stone-400">
                            Something you prepare in batches, like brewed tea or cooked pearls.
                        </p>
                    </div>


                    <div className="flex flex-col gap-5">

                        <div>
                            <label className={labelStyle}>Name</label>

                            <input
                                type="text"
                                value={ingredientForm.name}
                                onChange={(event) => setIngredientForm({ ...ingredientForm, name: event.target.value })}
                                placeholder="Thai Tea"
                                className={inputStyle}
                            />
                        </div>

                        <div>
                            <label className={labelStyle}>Unit</label>

                            <select
                                value={ingredientForm.base_unit}
                                onChange={(event) => setIngredientForm({ ...ingredientForm, base_unit: event.target.value as Ingredient["base_unit"] })}
                                className={inputStyle}
                            >
                                <option value="ml">Milliliters (ml)</option>
                                <option value="g">Grams (g)</option>
                                <option value="oz">Ounces (oz)</option>
                            </select>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className={labelStyle}>Batch size ({ingredientForm.base_unit})</label>

                                <input
                                    type="number"
                                    min="0"
                                    step="any"
                                    value={ingredientForm.default_batch_quantity}
                                    onChange={(event) => setIngredientForm({ ...ingredientForm, default_batch_quantity: event.target.value })}
                                    placeholder="4000"
                                    className={inputStyle}
                                />
                            </div>

                            <div>
                                <label className={labelStyle}>Per serving ({ingredientForm.base_unit})</label>

                                <input
                                    type="number"
                                    min="0"
                                    step="any"
                                    value={ingredientForm.quantity_per_serving}
                                    onChange={(event) => setIngredientForm({ ...ingredientForm, quantity_per_serving: event.target.value })}
                                    placeholder="500"
                                    className={inputStyle}
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className={labelStyle}>Prep time (min)</label>

                                <input
                                    type="number"
                                    min="0"
                                    step="1"
                                    value={ingredientForm.preparation_time}
                                    onChange={(event) => setIngredientForm({ ...ingredientForm, preparation_time: event.target.value })}
                                    placeholder="20"
                                    className={inputStyle}
                                />
                            </div>

                            <div>
                                <label className={labelStyle}>Shelf life (min)</label>

                                <input
                                    type="number"
                                    min="1"
                                    step="1"
                                    value={ingredientForm.default_shelf_life}
                                    onChange={(event) => setIngredientForm({ ...ingredientForm, default_shelf_life: event.target.value })}
                                    placeholder="4320"
                                    className={inputStyle}
                                />

                                <p className="mt-2 text-xs text-stone-400">
                                    4 hours = 240, 3 days = 4320
                                </p>
                            </div>
                        </div>

                        <Toggle
                            label="Needs cooling before serving"
                            checked={ingredientForm.requires_cooling}
                            onChange={(checked) => setIngredientForm({ ...ingredientForm, requires_cooling: checked })}
                        />

                        {ingredientForm.requires_cooling && (
                            <div>
                                <label className={labelStyle}>Cooling time (min)</label>

                                <input
                                    type="number"
                                    min="0"
                                    step="1"
                                    value={ingredientForm.cooling_time}
                                    onChange={(event) => setIngredientForm({ ...ingredientForm, cooling_time: event.target.value })}
                                    placeholder="20"
                                    className={inputStyle}
                                />
                            </div>
                        )}

                        <Toggle
                            label="Topping customers can add"
                            checked={ingredientForm.is_topping}
                            onChange={(checked) => setIngredientForm({ ...ingredientForm, is_topping: checked })}
                        />

                        <Toggle
                            label="Active"
                            checked={ingredientForm.is_active}
                            onChange={(checked) => setIngredientForm({ ...ingredientForm, is_active: checked })}
                        />

                        {ingredientMessage && (
                            <p className="text-sm text-stone-500">
                                {ingredientMessage}
                            </p>
                        )}

                        <div className="flex gap-2">
                            <button
                                type="button"
                                onClick={saveIngredient}
                                disabled={isSaving}
                                className="mt-2 flex-1 rounded-full bg-[#dcecee] px-5 py-3 text-sm font-semibold text-stone-700 transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                                {editingIngredientId === null ? "Add ingredient" : "Save ingredient"}
                            </button>

                            {editingIngredientId !== null && (
                                <button
                                    type="button"
                                    onClick={resetIngredientForm}
                                    className="mt-2 rounded-full border border-stone-200 px-5 py-3 text-sm font-semibold text-stone-500 transition hover:brightness-95"
                                >
                                    Cancel
                                </button>
                            )}
                        </div>

                    </div>
                </section>


                <section className="overflow-hidden rounded-3xl border border-stone-200 bg-[#FFFDF7]">

                    <div className="border-b border-stone-200 px-6 py-5">
                        <h2 className="text-lg font-semibold text-stone-800">
                            Ingredients
                        </h2>

                        <p className="mt-1 text-sm text-stone-400">
                            Hidden ingredients stay in your history but can't be used for new batches or orders.
                        </p>
                    </div>


                    {/* Empty state for a new shop */}

                    {ingredients.length === 0 && (
                        <div className="px-6 py-10 text-center">
                            <p className="text-sm font-medium text-stone-500">
                                Add your first ingredient, like Thai tea or tapioca pearls
                            </p>

                            <p className="mt-1 text-xs text-stone-400">
                                Ingredients are what you make in batches. Drinks are what customers order, made from your ingredients.
                            </p>
                        </div>
                    )}


                    {ingredients.map((ingredient) => (
                        <div
                            key={ingredient.id}
                            className="flex items-center justify-between gap-4 border-t border-stone-100 px-6 py-5"
                        >
                            <div>
                                <div className="flex items-center gap-2">
                                    <p className="font-medium text-stone-800">
                                        {ingredient.name}
                                    </p>

                                    {ingredient.is_topping && (
                                        <span className="rounded-full bg-pink-100 px-3 py-1 text-xs font-semibold text-pink-500">
                                            Topping
                                        </span>
                                    )}
                                </div>

                                <p className="mt-1 text-xs text-stone-400">
                                    {Number(ingredient.default_batch_quantity).toLocaleString()} {ingredient.base_unit} batch
                                    {" · "}
                                    {Number(ingredient.quantity_per_serving).toLocaleString()} {ingredient.base_unit} per serving
                                </p>

                                <p className="mt-1 text-xs text-stone-400">
                                    Prep {formatMinutes(ingredient.preparation_time)}
                                    {ingredient.requires_cooling && ` · Cools ${formatMinutes(ingredient.cooling_time)}`}
                                    {" · "}
                                    Lasts {formatMinutes(ingredient.default_shelf_life)}
                                </p>
                            </div>

                            <div className="flex items-center gap-2">
                                <button
                                    type="button"
                                    onClick={() => toggleIngredient(ingredient)}
                                    className={`rounded-full px-3 py-1 text-xs font-semibold ${ingredient.is_active ? "bg-green-100 text-green-700" : "bg-stone-100 text-stone-600"}`}
                                >
                                    {ingredient.is_active ? "Active" : "Hidden"}
                                </button>

                                <button
                                    type="button"
                                    onClick={() => editIngredient(ingredient)}
                                    className="rounded-full bg-[#dcecee] px-4 py-2 text-xs font-semibold text-stone-700 hover:brightness-95"
                                >
                                    Edit
                                </button>
                            </div>
                        </div>
                    ))}

                </section>

            </div>


            {/* Drinks */}

            <div className="grid gap-6 xl:grid-cols-[1fr_2fr]">

                <section className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">

                    <div className="mb-6">
                        <h2 className="text-lg font-semibold text-stone-800">
                            {editingDrinkId === null ? "Add a drink" : "Edit drink"}
                        </h2>

                        <p className="mt-1 text-sm text-stone-400">
                            Something customers order, and the ingredients in one serving.
                        </p>
                    </div>


                    <div className="flex flex-col gap-5">

                        <div>
                            <label className={labelStyle}>Name</label>

                            <input
                                type="text"
                                value={drinkForm.name}
                                onChange={(event) => setDrinkForm({ ...drinkForm, name: event.target.value })}
                                placeholder="Thai Milk Tea"
                                className={inputStyle}
                            />
                        </div>


                        {/* Recipe rows: one ingredient and its amount each */}

                        <div>
                            <label className={labelStyle}>Recipe</label>

                            <div className="flex flex-col gap-3">
                                {drinkForm.recipe.map((row, index) => (
                                    <div key={index} className="grid grid-cols-[2fr_1fr_auto] items-center gap-2">
                                        <select
                                            value={row.prepared_item_id ?? ""}
                                            onChange={(event) => updateRecipeRow(index, { prepared_item_id: Number(event.target.value) })}
                                            className={inputStyle}
                                        >
                                            <option value="" disabled>
                                                Select an ingredient
                                            </option>

                                            {getRecipeOptions(row).map((ingredient) => (
                                                <option key={ingredient.id} value={ingredient.id}>
                                                    {ingredient.name}
                                                </option>
                                            ))}
                                        </select>

                                        <input
                                            type="number"
                                            min="0"
                                            step="any"
                                            value={row.quantity}
                                            onChange={(event) => updateRecipeRow(index, { quantity: event.target.value })}
                                            placeholder={getIngredientUnit(row.prepared_item_id) || "Amount"}
                                            className={inputStyle}
                                        />

                                        <button
                                            type="button"
                                            onClick={() => removeRecipeRow(index)}
                                            disabled={drinkForm.recipe.length === 1}
                                            className="rounded-full border border-stone-200 px-3 py-2 text-xs font-semibold text-stone-500 hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50"
                                        >
                                            Remove
                                        </button>
                                    </div>
                                ))}
                            </div>

                            <button
                                type="button"
                                onClick={addRecipeRow}
                                className="mt-3 rounded-full bg-[#dcecee] px-4 py-2 text-xs font-semibold text-stone-700 hover:brightness-95"
                            >
                                Add ingredient
                            </button>
                        </div>

                        <Toggle
                            label="Active"
                            checked={drinkForm.is_active}
                            onChange={(checked) => setDrinkForm({ ...drinkForm, is_active: checked })}
                        />

                        {drinkMessage && (
                            <p className="text-sm text-stone-500">
                                {drinkMessage}
                            </p>
                        )}

                        <div className="flex gap-2">
                            <button
                                type="button"
                                onClick={saveDrink}
                                disabled={isSaving || ingredients.length === 0}
                                className="mt-2 flex-1 rounded-full bg-[#dcecee] px-5 py-3 text-sm font-semibold text-stone-700 transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                                {editingDrinkId === null ? "Add drink" : "Save drink"}
                            </button>

                            {editingDrinkId !== null && (
                                <button
                                    type="button"
                                    onClick={resetDrinkForm}
                                    className="mt-2 rounded-full border border-stone-200 px-5 py-3 text-sm font-semibold text-stone-500 transition hover:brightness-95"
                                >
                                    Cancel
                                </button>
                            )}
                        </div>

                    </div>
                </section>


                <section className="overflow-hidden rounded-3xl border border-stone-200 bg-[#FFFDF7]">

                    <div className="border-b border-stone-200 px-6 py-5">
                        <h2 className="text-lg font-semibold text-stone-800">
                            Drinks
                        </h2>

                        <p className="mt-1 text-sm text-stone-400">
                            Hidden drinks stay in your order history but can't be ordered.
                        </p>
                    </div>


                    {drinks.length === 0 && (
                        <div className="px-6 py-10 text-center">
                            <p className="text-sm font-medium text-stone-500">
                                No drinks yet.
                            </p>

                            <p className="mt-1 text-xs text-stone-400">
                                {ingredients.length === 0
                                    ? "Add an ingredient first, then build a drink from it."
                                    : "Add a drink and pick the ingredients in one serving."}
                            </p>
                        </div>
                    )}


                    {drinks.map((drink) => (
                        <div
                            key={drink.id}
                            className="flex items-center justify-between gap-4 border-t border-stone-100 px-6 py-5"
                        >
                            <div>
                                <p className="font-medium text-stone-800">
                                    {drink.name}
                                </p>

                                <p className="mt-1 text-xs text-stone-400">
                                    {drink.recipe
                                        .map((row) => `${getIngredientName(row.prepared_item_id)} ${Number(row.quantity).toLocaleString()} ${getIngredientUnit(row.prepared_item_id)}`)
                                        .join(" · ")}
                                </p>
                            </div>

                            <div className="flex items-center gap-2">
                                <button
                                    type="button"
                                    onClick={() => toggleDrink(drink)}
                                    className={`rounded-full px-3 py-1 text-xs font-semibold ${drink.is_active ? "bg-green-100 text-green-700" : "bg-stone-100 text-stone-600"}`}
                                >
                                    {drink.is_active ? "Active" : "Hidden"}
                                </button>

                                <button
                                    type="button"
                                    onClick={() => editDrink(drink)}
                                    className="rounded-full bg-[#dcecee] px-4 py-2 text-xs font-semibold text-stone-700 hover:brightness-95"
                                >
                                    Edit
                                </button>
                            </div>
                        </div>
                    ))}

                </section>

            </div>

        </div>
    );
}


export default Menu;
