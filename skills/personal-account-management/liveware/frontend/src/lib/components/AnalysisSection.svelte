<script lang="ts">
  import BrainCircuitIcon from "@lucide/svelte/icons/brain-circuit";
  import CircleCheckIcon from "@lucide/svelte/icons/circle-check";
  import LoaderCircleIcon from "@lucide/svelte/icons/loader-circle";
  import TriangleAlertIcon from "@lucide/svelte/icons/triangle-alert";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import * as Card from "$lib/components/ui/card";
  import { formatMonth } from "$lib/format";
  import type { TranslationKey } from "$lib/i18n";
  import type { AnalysisStatus, Language } from "$lib/types";

  type Props = {
    analysis: AnalysisStatus;
    analysisLaunching: boolean;
    selectedMonth: string;
    language: Language;
    t: (key: TranslationKey) => string;
    onRun: () => void | Promise<void>;
  };

  let {
    analysis,
    analysisLaunching,
    selectedMonth,
    language,
    t,
    onRun,
  }: Props = $props();

  const displayedMonth = $derived(
    /\b\d{4}-(0[1-9]|1[0-2])\b/.exec(analysis.window)?.[0] ?? selectedMonth,
  );
  const isRunning = $derived(analysis.state === "running" || analysis.busy);
  const actionDisabled = $derived(isRunning || analysisLaunching || !selectedMonth);

  function elapsedLabel(seconds: number): string {
    const safe = Math.max(0, Math.round(seconds || 0));
    const minutes = Math.floor(safe / 60);
    const remaining = safe % 60;
    return minutes > 0
      ? `${minutes}${t("minutesShort")} ${remaining}${t("secondsShort")}`
      : `${remaining}${t("secondsShort")}`;
  }

  function failureMessage(): string {
    const code = analysis.error?.code;
    if (code === "analysis_client_timeout") return t("analysisClientTimeoutDetail");
    if (code === "analysis_timeout") return t("analysisTimeoutDetail");
    if (code === "upstream_failed") return t("analysisServiceFailedDetail");
    if (["report_failed", "report_missing", "report_publish_failed"].includes(code ?? "")) {
      return t("analysisReportFailedDetail");
    }
    if (["template_missing", "prompt_render_failed"].includes(code ?? "")) {
      return t("analysisSetupFailedDetail");
    }
    return t("analysisFailedDetail");
  }

  function stateLabel(): string {
    if (isRunning) return t("analysisRunning");
    if (analysisLaunching) return t("analysisStarting");
    if (analysis.state === "succeeded") return t("analysisSucceeded");
    if (analysis.state === "failed") return t("analysisFailed");
    return t("analysisReady");
  }
</script>

<section class="grid gap-4" aria-labelledby="analysis-title">
  <div class="flex items-end justify-between gap-4 max-[45rem]:flex-col max-[45rem]:items-start">
    <div>
      <p class="mb-0.5 font-mono text-xs font-semibold uppercase tracking-widest text-muted-foreground">{t("navAnalysis")}</p>
      <h2 id="analysis-title" class="text-3xl font-semibold tracking-tight sm:text-4xl">{t("analysisTitle")}</h2>
      <p class="mt-1 max-w-2xl text-muted-foreground">{t("analysisDescription")}</p>
    </div>
  </div>

  <Card.Root class="min-h-80 overflow-hidden data-[state=succeeded]:border-primary/40 data-[state=failed]:border-destructive/50" data-state={analysis.state} aria-live="polite" aria-busy={isRunning || analysisLaunching}>
    <Card.Header>
      <div class="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 max-[45rem]:grid-cols-[auto_minmax(0,1fr)] max-[45rem]:[&>[data-slot=badge]]:col-span-full max-[45rem]:[&>[data-slot=badge]]:justify-self-start">
        <div class="grid size-11 place-items-center rounded-lg bg-muted text-primary data-[failed=true]:text-destructive [&_svg]:size-5" data-failed={analysis.state === "failed"} aria-hidden="true">
          {#if isRunning || analysisLaunching}
            <LoaderCircleIcon class="animate-spin motion-reduce:animate-none" />
          {:else if analysis.state === "succeeded"}
            <CircleCheckIcon />
          {:else if analysis.state === "failed"}
            <TriangleAlertIcon />
          {:else}
            <BrainCircuitIcon />
          {/if}
        </div>
        <div>
          <Card.Title>{stateLabel()}</Card.Title>
          <Card.Description>
            {t("analysisForMonth")} {formatMonth(displayedMonth, language)}
          </Card.Description>
        </div>
        <Badge variant={analysis.state === "failed" ? "destructive" : "outline"}>
          {stateLabel()}
        </Badge>
      </div>
    </Card.Header>

    <Card.Content class="flex min-h-44 flex-1 flex-col justify-between gap-2">
      {#if isRunning}
        <p class="max-w-3xl text-base leading-relaxed break-words sm:text-lg">{t("analysisRunningDetail")}</p>
        <small class="font-mono text-muted-foreground">{t("analysisElapsed")} {elapsedLabel(analysis.elapsed_s)}</small>
      {:else if analysisLaunching}
        <p class="max-w-3xl text-base leading-relaxed break-words sm:text-lg">{t("analysisStarting")}</p>
      {:else if analysis.state === "succeeded"}
        <p class="max-w-3xl text-base leading-relaxed break-words sm:text-lg">{t("analysisSucceededDetail")}</p>
      {:else if analysis.state === "failed"}
        <p class="max-w-3xl text-base leading-relaxed break-words sm:text-lg">{failureMessage()}</p>
      {:else}
        <p class="max-w-3xl text-base leading-relaxed break-words sm:text-lg">{t("analysisReadyDetail")}</p>
      {/if}

      <div class="mt-auto flex flex-wrap gap-3 pt-6 max-[45rem]:w-full max-[45rem]:[&_[data-slot=button]]:w-full">
        {#if analysis.state === "succeeded" && analysis.report_url}
          <Button href={`#/reports/${displayedMonth}`}>
            {t("analysisOpenReport")}
          </Button>
        {/if}
        <Button href="#/reports" variant="outline">
          {t("analysisAllReports")}
        </Button>
        <Button
          variant={analysis.state === "succeeded" ? "outline" : "default"}
          disabled={actionDisabled}
          onclick={() => void onRun()}
        >
          {analysis.state === "failed" ? t("analysisRetry") : t("analysisRun")}
        </Button>
      </div>
    </Card.Content>
  </Card.Root>
</section>
