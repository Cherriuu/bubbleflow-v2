import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/auth";

function Register() {
    const { status, register } = useAuth();
    const navigate = useNavigate();

    const [shopName, setShopName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    if (status === "logged_in") {
        return <Navigate to="/" replace />;
    }

    async function handleRegister(event: FormEvent) {
        event.preventDefault();
        setIsSubmitting(true);
        setMessage("");

        const error = await register(shopName, email, password);

        setIsSubmitting(false);

        if (error) {
            setMessage(error);
            return;
        }

        navigate("/", { replace: true });
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-[#FAF8F2] px-4 py-8">

            <div className="w-full max-w-md">

                <div className="mb-8 text-center">
                    <p className="mb-2 text-4xl font-bold tracking-tight text-pink-300">
                        BubbleFlow
                    </p>

                    <h1 className="text-2xl font-bold tracking-tight text-stone-800">
                        Register your shop
                    </h1>

                    <p className="mt-3 text-base text-stone-500">
                        One login for your shop that everyone on your team can share.
                    </p>
                </div>


                <section className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">

                    <form onSubmit={handleRegister} className="flex flex-col gap-5">

                        <div>
                            <label htmlFor="shop-name" className="mb-2 block text-sm font-medium text-stone-600">
                                Shop name
                            </label>

                            <input
                                id="shop-name"
                                type="text"
                                autoComplete="organization"
                                required
                                maxLength={120}
                                value={shopName}
                                onChange={(event) => setShopName(event.target.value)}
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                            />
                        </div>

                        <div>
                            <label htmlFor="email" className="mb-2 block text-sm font-medium text-stone-600">
                                Email
                            </label>

                            <input
                                id="email"
                                type="email"
                                autoComplete="email"
                                required
                                maxLength={150}
                                value={email}
                                onChange={(event) => setEmail(event.target.value)}
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                            />
                        </div>

                        <div>
                            <label htmlFor="password" className="mb-2 block text-sm font-medium text-stone-600">
                                Password
                            </label>

                            <input
                                id="password"
                                type="password"
                                autoComplete="new-password"
                                required
                                minLength={8}
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                            />

                            <p className="mt-2 text-xs text-stone-400">
                                At least 8 characters, not only numbers, and not too close to your email.
                            </p>
                        </div>

                        {message && (
                            <p className="text-sm text-stone-500">
                                {message}
                            </p>
                        )}

                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="mt-2 rounded-full bg-[#dcecee] px-5 py-3 text-sm font-semibold text-stone-700 transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {isSubmitting ? "Creating your shop..." : "Create shop"}
                        </button>

                    </form>
                </section>


                <p className="mt-6 text-center text-sm text-stone-500">
                    Already registered?{" "}
                    <Link to="/login" className="font-semibold text-stone-700 hover:text-stone-900">
                        Log in
                    </Link>
                </p>

            </div>
        </div>
    );
}

export default Register;
