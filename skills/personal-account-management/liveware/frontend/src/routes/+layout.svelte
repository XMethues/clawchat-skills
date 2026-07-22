<script lang="ts">
  import { page } from "$app/state";
  import { onMount, setContext } from "svelte";
  import { toast } from "svelte-sonner";
  import DashboardHeader from "$lib/components/DashboardHeader.svelte";
  import EmptyState from "$lib/components/EmptyState.svelte";
  import { Toaster } from "$lib/components/ui/sonner";
  import {
    DASHBOARD_APP_CONTEXT,
    type DashboardAppContext,
  } from "$lib/app-context";
  import { dashboardController as controller } from "$lib/dashboard-controller.svelte";
  import { languageFromSearch, loadErrorDescriptionKey, translator } from "$lib/i18n";
  import type { DashboardSection } from "$lib/types";
  import "../app.css";

  let { children } = $props();

  const language = languageFromSearch();
  const t = translator(language);
  const context: DashboardAppContext = { language, t };
  setContext(DASHBOARD_APP_CONTEXT, context);

  const loadErrorDescription = $derived(t(loadErrorDescriptionKey(controller.error)));
  const activeSection = $derived.by<DashboardSection>(() => {
    const routeId = page.route.id ?? "/";
    if (routeId.startsWith("/transactions")) return "transactions";
    if (routeId.startsWith("/subscriptions")) return "subscriptions";
    if (routeId.startsWith("/analysis") || routeId.startsWith("/reports")) return "analysis";
    return "overview";
  });
  let outageToastShown = false;

  $effect(() => {
    if (!controller.error) {
      outageToastShown = false;
    } else if (controller.book && !outageToastShown) {
      outageToastShown = true;
      toast.error(t("loadError"), { description: loadErrorDescription });
    }
  });

  onMount(() => {
    document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
    controller.start();
    return () => controller.stop();
  });
</script>

<svelte:head>
  <title>{t("appTitle")}</title>
  <meta name="description" content={t("appDescription")} />
</svelte:head>

<div class="min-h-screen">
  <DashboardHeader
    {language}
    months={controller.months}
    selectedMonth={controller.selectedMonth}
    {activeSection}
    {t}
    onMonthChange={(month) => controller.selectMonth(month)}
  />

  {#if controller.initialLoading}
    <main class="mx-auto grid min-h-[55vh] w-full max-w-6xl place-items-center px-3 text-muted-foreground sm:px-4" aria-live="polite">
      <div>
        <div class="mx-auto mb-3 size-9 animate-spin rounded-full border-3 border-border border-t-primary motion-reduce:animate-none" aria-hidden="true"></div>
        <p>{t("loading")}</p>
      </div>
    </main>
  {:else if controller.error && !controller.book}
    <main class="mx-auto grid w-full max-w-6xl gap-5 px-3 py-6 sm:px-4 sm:py-8">
      <EmptyState
        role="alert"
        title={t("loadError")}
        description={loadErrorDescription}
        actionLabel={t("retry")}
        onAction={() => void controller.refresh({ refreshMonths: true })}
      />
    </main>
  {:else if !controller.book}
    <main class="mx-auto grid min-h-[55vh] w-full max-w-6xl place-items-center px-3 text-muted-foreground sm:px-4" aria-live="polite">
      <div>
        <div class="mx-auto mb-3 size-9 animate-spin rounded-full border-3 border-border border-t-primary motion-reduce:animate-none" aria-hidden="true"></div>
        <p>{t("loading")}</p>
      </div>
    </main>
  {:else}
    <main class="mx-auto grid w-full max-w-6xl gap-5 px-3 py-6 sm:px-4 sm:py-8">
      {@render children()}
    </main>
  {/if}

  <Toaster position="top-right" richColors closeButton />
</div>
