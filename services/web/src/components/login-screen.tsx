import { Eye, EyeOff, KeyRound, Loader2, ShieldCheck } from "lucide-react";
import { useState, type SubmitEvent } from "react";

import { Brand } from "@/components/brand";
import { FormError } from "@/components/form-fields";
import { ServiceStatus } from "@/components/service-status";
import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLogin } from "@/hooks/use-session";

export function LoginScreen() {
  const [apiKey, setApiKey] = useState("");
  const [visible, setVisible] = useState(false);
  const login = useLogin();
  const error = login.error?.message ?? null;

  const submit = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (apiKey.trim()) login.mutate(apiKey.trim());
  };

  return (
    <div className="flex min-h-dvh flex-col lg:flex-row">
      <aside className="flex flex-col gap-10 bg-ink px-6 py-5 text-ink-foreground lg:w-[46%] lg:justify-between lg:px-14 lg:py-12">
        <Brand inverted />
        <NetworkArt className="hidden w-full max-w-lg lg:block" />
        <div className="hidden max-w-md space-y-3 lg:block">
          <p className="text-3xl leading-tight font-bold tracking-tight text-balance">
            La red de atención, clara en un vistazo.
          </p>
          <p className="text-base text-pretty text-ink-muted">
            Consulte qué zonas cubre cada base y cuál es la ruta de menor tiempo para enviar a un
            técnico.
          </p>
        </div>
      </aside>
      <main className="relative flex flex-1 flex-col items-center justify-center gap-5 px-4 py-10">
        <div className="absolute top-3 right-3">
          <ThemeToggle />
        </div>
        <Card className="w-full max-w-sm">
          <CardHeader>
            <h1 className="text-2xl font-bold tracking-tight text-ink dark:text-foreground">
              Bienvenido
            </h1>
            <CardDescription className="text-pretty">
              Ingrese su clave de acceso para consultar y administrar la red de atención.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4" onSubmit={submit} noValidate>
              <div className="grid gap-2">
                <Label htmlFor="api-key">Clave de acceso</Label>
                <div className="relative">
                  <KeyRound
                    className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
                    aria-hidden
                  />
                  <Input
                    id="api-key"
                    type={visible ? "text" : "password"}
                    autoComplete="off"
                    spellCheck={false}
                    autoFocus
                    className="h-11 pr-11 pl-9 font-mono"
                    value={apiKey}
                    onChange={(event) => {
                      setApiKey(event.target.value);
                    }}
                    aria-invalid={error ? true : undefined}
                    aria-describedby={error ? "api-key-error" : undefined}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute top-0 right-0 size-11"
                    aria-label={visible ? "Ocultar la clave" : "Mostrar la clave"}
                    aria-pressed={visible}
                    onClick={() => {
                      setVisible((value) => !value);
                    }}
                  >
                    {visible ? <EyeOff /> : <Eye />}
                  </Button>
                </div>
                <FormError id="api-key-error" message={error} />
              </div>
              <Button
                type="submit"
                className="h-11 w-full text-base"
                disabled={login.isPending || !apiKey.trim()}
              >
                {login.isPending && <Loader2 className="animate-spin" aria-hidden />}
                Entrar
              </Button>
              <p className="flex items-start gap-2 text-xs text-pretty text-muted-foreground">
                <ShieldCheck className="mt-0.5 size-3.5 shrink-0" aria-hidden />
                Si no tiene una clave, pídasela a quien administra el sistema. Su clave no se guarda
                en este navegador.
              </p>
            </form>
          </CardContent>
        </Card>
        <ServiceStatus />
      </main>
    </div>
  );
}

/** Ilustración decorativa: la red con una ruta resaltada en el color de marca. */
function NetworkArt({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 520 300" className={className} aria-hidden>
      <g className="stroke-[#2b4767]" strokeWidth="2" fill="none">
        <path d="M70 90 L190 60 L290 120 L250 210 L120 220 Z" />
        <path d="M290 120 L410 80 L460 190 L350 250 L250 210" />
        <path d="M190 60 L250 210" />
      </g>
      <path
        d="M70 90 L190 60 L290 120 L410 80"
        className="stroke-brand"
        strokeWidth="3.5"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <g className="fill-ink stroke-[#7f95ae]" strokeWidth="2">
        <circle cx="120" cy="220" r="9" />
        <circle cx="250" cy="210" r="9" />
        <circle cx="460" cy="190" r="9" />
        <circle cx="350" cy="250" r="9" />
      </g>
      <g className="fill-ink-foreground stroke-brand" strokeWidth="3">
        <circle cx="190" cy="60" r="9" />
        <circle cx="290" cy="120" r="9" />
        <circle cx="410" cy="80" r="11" />
      </g>
      <rect x="57" y="77" width="26" height="26" rx="6" className="fill-brand" />
    </svg>
  );
}
