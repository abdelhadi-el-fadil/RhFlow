"use client"

import { LoginForm } from "@/components/login-form"
import Image from "next/image"

export default function LoginPage() {
  return (
    <div className="grid min-h-svh md:grid-cols-2">
      <div className="flex flex-col items-center justify-center gap-8 p-6 md:p-10">
        <div className="text-center">
          <p className="bg-gradient-to-r from-slate-900 via-teal-700 to-emerald-700 bg-clip-text text-5xl font-black tracking-tight text-transparent md:text-6xl">
            RhFlow
          </p>
        </div>
        <div className="flex w-full items-center justify-center">
          <div className="w-full max-w-xs">
            <LoginForm />
          </div>
        </div>
      </div>
      <div className="relative min-h-[260px] bg-muted md:min-h-svh">
        <Image
          src="/rhflow.png"
          alt="RhFlow"
          fill
          unoptimized
          priority
          sizes="(min-width: 768px) 50vw, 100vw"
          className="object-contain p-10"
        />
      </div>
    </div>
  )
}