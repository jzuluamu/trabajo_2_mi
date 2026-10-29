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
    <div className="relative grid min-h-dvh place-items-center px-4 py-10">
      <div className="absolute top-3 right-3">
        <ThemeToggle />
      </div>
      <main className="w-full max-w-sm space-y-6">
        <Brand />
        <Card>
          <CardHeader>
            <h1 className="text-xl font-semibold tracking-tight">Bienvenido</h1>
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
                    className="h-11 pr-11 pl-9 font-mono sm:h-9"
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
                    className="absolute top-0 right-0 size-11 sm:size-9"
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
                className="h-11 w-full sm:h-9"
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
