<script lang="ts">
  import ArrowLeftIcon from "@lucide/svelte/icons/arrow-left";
  import { page } from "$app/state";
  import { fetchReport } from "$lib/api";
  import { getDashboardAppContext } from "$lib/app-context";
  import EmptyState from "$lib/components/EmptyState.svelte";
  import { Button } from "$lib/components/ui/button";
  import { formatMonth } from "$lib/format";
  import type { ReportDocument } from "$lib/types";

  const { language, t } = getDashboardAppContext();
  const month = $derived(page.params.month ?? "");
  let report = $state<ReportDocument | null>(null);
  let loading = $state(true);
  let failed = $state(false);

  $effect(() => {
    const requestedMonth = month;
    const abortController = new AbortController();
    loading = true;
    failed = false;
    report = null;

    if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(requestedMonth)) {
      loading = false;
      failed = true;
    } else {
      void fetchReport(requestedMonth, abortController.signal)
        .then((result) => {
          report = result;
        })
        .catch((error: unknown) => {
          if (!(error instanceof DOMException && error.name === "AbortError")) failed = true;
        })
        .finally(() => {
          if (!abortController.signal.aborted) loading = false;
        });
    }

    return () => abortController.abort();
  });
</script>

<section class="grid gap-4" aria-labelledby="report-title">
  <div class="flex flex-col items-start gap-3">
    <Button href="#/reports" variant="ghost" size="sm">
      <ArrowLeftIcon data-icon="inline-start" />
      {t("reportBack")}
    </Button>
    <div>
      <p class="mb-0.5 font-mono text-xs font-semibold uppercase tracking-widest text-muted-foreground">{t("reportsEyebrow")}</p>
      <h2 id="report-title" class="text-3xl font-semibold tracking-tight sm:text-4xl">
        {formatMonth(month, language)}
      </h2>
    </div>
  </div>

  {#if loading}
    <div class="grid min-h-64 place-items-center text-muted-foreground" aria-live="polite">
      <div>
        <div class="mx-auto mb-3 size-9 animate-spin rounded-full border-3 border-border border-t-primary motion-reduce:animate-none" aria-hidden="true"></div>
        <p>{t("reportLoading")}</p>
      </div>
    </div>
  {:else if failed || !report}
    <EmptyState
      role="alert"
      title={t("reportLoadError")}
      description={t("loadErrorUnavailable")}
      actionLabel={t("reportBack")}
      onAction={() => {
        window.location.hash = "/reports";
      }}
    />
  {:else}
    <iframe
      class="min-h-[75vh] w-full rounded-md border bg-background"
      title={`${t("reportFrameTitle")} — ${formatMonth(report.month, language)}`}
      srcdoc={report.html}
      sandbox=""
      referrerpolicy="no-referrer"
    ></iframe>
  {/if}
</section>
