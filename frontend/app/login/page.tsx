import { LoginForm } from "@/components/login-form"

export default function LoginPage() {
  return (
    <div className="relative flex min-h-svh items-center justify-center bg-gradient-to-r from-sky-900 to-teal-300 p-4 sm:p-6 lg:p-12">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.18),transparent_40%),radial-gradient(circle_at_80%_80%,rgba(131,208,203,0.20),transparent_45%)]" />
      <div className="relative w-full max-w-xl">
        <LoginForm />
      </div>
    </div>
  )
}