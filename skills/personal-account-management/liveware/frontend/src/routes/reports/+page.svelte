<script lang="ts">
  import FileTextIcon from "@lucide/svelte/icons/file-text";
  import { onMount } from "svelte";
  import { fetchReports } from "$lib/api";
  import { getDashboardAppContext } from "$lib/app-context";
  import EmptyState from "$lib/components/EmptyState.svelte";
  import { Button } from "$lib/components/ui/button";
  import * as Card from "$lib/components/ui/card";
  import { formatMonth } from "$lib/format";
  import type { ReportSummary } from "$lib/types";

  const { language, t } = getDashboardAppContext();
  let reports = $state<ReportSummary[]>([]);
  let loading = $state(true);
  let failed = $state(false);

  function modifiedLabel(timestamp: number): string {
    return new Intl.DateTimeFormat(language === "zh" ? "zh-CN" : "en", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(timestamp * 1000));
  }

  async function loadReports(): Promise<void> {
    loading = true;
    failed = false;
    try {
      reports = (await fetchReports()).reports;
    } catch {
      failed = true;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    void loadReports();
  });
</script>

<section class="grid gap-4" aria-labelledby="reports-title">
  <div>
    <p class="mb-0.5 font-mono text-xs font-semibold uppercase tracking-widest text-muted-foreground">{t("reportsEyebrow")}</p>
    <h2 id="reports-title" class="text-3xl font-semibold tracking-tight sm:text-4xl">{t("reportsTitle")}</h2>
    <p class="mt-1 max-w-2xl text-muted-foreground">{t("reportsDescription")}</p>
  </div>

  {#if loading}
    <div class="grid min-h-64 place-items-center text-muted-foreground" aria-live="polite">
      <div>
        <div class="mx-auto mb-3 size-9 animate-spin rounded-full border-3 border-border border-t-primary motion-reduce:animate-none" aria-hidden="true"></div>
        <p>{t("reportLoading")}</p>
      </div>
    </div>
  {:else if failed}
    <EmptyState
      role="alert"
      title={t("reportsLoadError")}
      description={t("loadErrorUnavailable")}
      actionLabel={t("retry")}
      onAction={() => void loadReports()}
    />
  {:else if reports.length === 0}
    <EmptyState
      title={t("reportsEmptyTitle")}
      description={t("reportsEmptyDescription")}
    />
  {:else}
    <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {#each reports as report (report.month)}
        <Card.Root>
          <Card.Header>
            <div class="mb-2 grid size-10 place-items-center rounded-lg bg-muted text-primary" aria-hidden="true">
              <FileTextIcon class="size-5" />
            </div>
            <Card.Title>{formatMonth(report.month, language)}</Card.Title>
            <Card.Description>{modifiedLabel(report.modified_at)}</Card.Description>
          </Card.Header>
          <Card.Footer>
            <Button href={`#/reports/${report.month}`} variant="outline" class="w-full">
              {t("reportOpen")}
            </Button>
          </Card.Footer>
        </Card.Root>
      {/each}
    </div>
  {/if}
</section>
