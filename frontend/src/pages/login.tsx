import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/auth";

function Login() {
    const { status, login, demoLogin } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Go back to the page the shop was trying to open, or the overview
    const nextPage = (location.state as { from?: string } | null)?.from ?? "/";

    if (status === "logged_in") {
        return <Navigate to={nextPage} replace />;
    }

    async function handleLogin(event: FormEvent) {
        event.preventDefault();
        setIsSubmitting(true);
        setMessage("");

        const error = await login(email, password);

        setIsSubmitting(false);

        if (error) {
            setMessage(error);
            return;
        }

        navigate(nextPage, { replace: true });
    }

    async function handleDemo() {
        setIsSubmitting(true);
        setMessage("");

        const error = await demoLogin();

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
                        Welcome back
                    </h1>

                    <p className="mt-3 text-base text-stone-500">
                        Log in to your shop to see today's inventory.
                    </p>
                </div>


                <section className="rounded-3xl border border-stone-200 bg-[#FFFDF7] p-6">

                    <form onSubmit={handleLogin} className="flex flex-col gap-5">

                        <div>
                            <label htmlFor="email" className="mb-2 block text-sm font-medium text-stone-600">
                                Email
                            </label>

                            <input
                                id="email"
                                type="email"
                                autoComplete="email"
                                required
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
                                autoComplete="current-password"
                                required
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                                className="w-full rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm text-stone-700 outline-none focus:border-pink-300"
                            />
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
                            {isSubmitting ? "Logging in..." : "Log in"}
                        </button>

                        <button
                            type="button"
                            onClick={handleDemo}
                            disabled={isSubmitting}
                            className="rounded-full bg-pink-300 px-5 py-3 text-sm font-semibold text-white transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            Try the demo
                        </button>

                    </form>
                </section>


                <p className="mt-6 text-center text-sm text-stone-500">
                    New to BubbleFlow?{" "}
                    <Link to="/register" className="font-semibold text-stone-700 hover:text-stone-900">
                        Register your shop
                    </Link>
                </p>

            </div>
        </div>
    );
}

export default Login;
