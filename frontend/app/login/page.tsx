import { LoginForm } from "@/components/login-form"

export default function LoginPage() {
  return (
    <div className="relative flex min-h-svh items-center justify-center bg-linear-to-br from-blue-100 via-indigo-100 to-violet-100 p-4 sm:p-6 lg:p-12">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_15%_15%,rgba(99,102,241,0.28),transparent_42%),radial-gradient(circle_at_85%_85%,rgba(139,92,246,0.25),transparent_45%)]" />
      <div className="relative w-full max-w-xl">
        <LoginForm />
      </div>
    </div>
  )
}
