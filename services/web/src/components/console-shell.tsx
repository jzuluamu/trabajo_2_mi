import { LogOut, Map as MapIcon, Radar, Settings2 } from "lucide-react";

import { AdminTab } from "@/components/admin/admin-tab";
import { Brand } from "@/components/brand";
import { CoverageTab } from "@/components/coverage/coverage-tab";
import { NetworkTab } from "@/components/network/network-tab";
import { ServiceStatus } from "@/components/service-status";
import { ErrorState, NetworkSkeleton } from "@/components/states";
import { ThemeToggle } from "@/components/theme-toggle";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useHashTab } from "@/hooks/use-hash-tab";
import { useNetwork } from "@/hooks/use-network";
import { ROLE_LABELS, useLogout } from "@/hooks/use-session";
import { describeError } from "@/lib/network-format";
import type { Role } from "@/lib/types";

const OPERATOR_TABS = ["red", "cobertura"] as const;
const COORDINATOR_TABS = ["red", "cobertura", "configurar"] as const;
type TabId = (typeof COORDINATOR_TABS)[number];

export function ConsoleShell({ role }: { role: Role }) {
  const isCoordinator = role === "coordinator";
  const [tab, setTab] = useHashTab<TabId>(isCoordinator ? COORDINATOR_TABS : OPERATOR_TABS, "red");
  const network = useNetwork();
  const logout = useLogout();

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-30 border-b bg-card/90 backdrop-blur">
        <div className="mx-auto flex h-16 w-full max-w-screen-2xl items-center gap-3 px-4 sm:px-6 lg:px-8">
          <Brand />
          <ServiceStatus className="ml-auto hidden md:flex" />
          <div className="ml-auto flex items-center gap-1 md:ml-2">
            <Badge variant="secondary" className="hidden sm:inline-flex">
              {ROLE_LABELS[role]}
            </Badge>
            <ThemeToggle />
            <Button
              variant="ghost"
              size="sm"
              className="h-11 sm:h-9"
              onClick={() => {
                logout.mutate();
              }}
              disabled={logout.isPending}
              aria-label="Cerrar sesión"
            >
              <LogOut aria-hidden />
              <span className="hidden sm:inline">Cerrar sesión</span>
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-screen-2xl flex-1 space-y-6 px-4 py-6 sm:px-6 lg:px-8">
        <h1 className="sr-only">ServicioCerca · Consola de operación</h1>
        <div className="flex flex-col gap-2 md:hidden">
          <p className="text-sm text-muted-foreground">
            Sesión: <span className="font-medium text-foreground">{ROLE_LABELS[role]}</span>
          </p>
          <ServiceStatus />
        </div>
        <Tabs value={tab} onValueChange={setTab} className="gap-6">
          <TabsList className="w-full justify-start overflow-x-auto group-data-[orientation=horizontal]/tabs:h-auto sm:w-fit">
            <TabsTrigger value="red" className="h-9 px-3">
              <MapIcon aria-hidden />
              Red
            </TabsTrigger>
            <TabsTrigger value="cobertura" className="h-9 px-3">
              <Radar aria-hidden />
              Cobertura
            </TabsTrigger>
            {isCoordinator && (
              <TabsTrigger value="configurar" className="h-9 px-3">
                <Settings2 aria-hidden />
                Configurar red
              </TabsTrigger>
            )}
          </TabsList>
          {network.isPending ? (
            <NetworkSkeleton />
          ) : network.isError ? (
            <ErrorState
              message={describeError(network.error)}
              onRetry={() => void network.refetch()}
            />
          ) : (
            <>
              <TabsContent value="red">
                <NetworkTab
                  network={network.data}
                  refreshing={network.isFetching}
                  onRefresh={() => void network.refetch()}
                  onConfigure={
                    isCoordinator
                      ? () => {
                          setTab("configurar");
                        }
                      : undefined
                  }
                />
              </TabsContent>
              <TabsContent value="cobertura">
                <CoverageTab network={network.data} />
              </TabsContent>
              {isCoordinator && (
                <TabsContent value="configurar">
                  <AdminTab network={network.data} />
                </TabsContent>
              )}
            </>
          )}
        </Tabs>
      </main>
    </div>
  );
}
