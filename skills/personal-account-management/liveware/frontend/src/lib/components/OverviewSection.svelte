<script lang="ts">
  import CashFlowChart from "$lib/components/CashFlowChart.svelte";
  import { Badge } from "$lib/components/ui/badge";
  import * as Card from "$lib/components/ui/card";
  import { formatMoney, formatMoneyWithCode, formatMonth, formatPercent } from "$lib/format";
  import type { TranslationKey } from "$lib/i18n";
  import {
    buildBudgetProgress,
    buildNaturalWeekBuckets,
    summarizeAccounts,
    summarizeCashFlow,
  } from "$lib/selectors";
  import type { BookResponse, Language } from "$lib/types";

  type Props = {
    book: BookResponse;
    language: Language;
    t: (key: TranslationKey) => string;
  };

  let { book, language, t }: Props = $props();

  const accounts = $derived(summarizeAccounts(book));
  const cashFlow = $derived(summarizeCashFlow(book));
  const budgets = $derived(buildBudgetProgress(book));
  const weeks = $derived(buildNaturalWeekBuckets(book));
  function accountTypeLabel(type: string): string {
    if (type === "liability") return t("liability");
    if (type === "receivable") return t("receivable");
    return t("asset");
  }
</script>

<section class="grid gap-4" aria-labelledby="overview-title">
  <div class="flex items-end justify-between gap-4 max-[45rem]:flex-col max-[45rem]:items-start">
    <div>
      <p class="mb-0.5 font-mono text-xs font-semibold uppercase tracking-widest text-muted-foreground">{formatMonth(book.dashboard_month, language)}</p>
      <h2 id="overview-title" class="text-3xl font-semibold tracking-tight sm:text-4xl">{t("navOverview")}</h2>
      <p class="mt-1 max-w-2xl text-muted-foreground">{t("overviewLead")}</p>
    </div>
  </div>

  <div class="grid gap-4 lg:grid-cols-[minmax(0,1.25fr)_minmax(18rem,0.75fr)]">
    <Card.Root class="min-h-[22rem] border-0 bg-foreground text-background shadow-lg [&_[data-slot=card-description]]:text-background/70">
      <Card.Header>
        <Card.Title>{t("baseNetWorth")}</Card.Title>
        <Card.Description>{t("baseNetWorthDescription")}</Card.Description>
      </Card.Header>
      <Card.Content class="flex flex-1 flex-col">
        <p class="mt-auto mb-6 text-5xl leading-none font-bold tracking-tighter break-words sm:text-6xl lg:text-7xl">
          {accounts.base_net_worth_minor === null
            ? "—"
            : formatMoney(accounts.base_net_worth_minor, accounts.base_currency, language)}
        </p>
        {#if accounts.available}
          <div class="grid gap-2 max-[45rem]:grid-cols-1 sm:grid-cols-3 [&>span]:grid [&>span]:gap-0.5 [&>span]:rounded-md [&>span]:border [&>span]:border-background/10 [&>span]:bg-background/5 [&>span]:p-3 [&>span]:text-xs [&>span]:text-background/70 [&_strong]:font-mono [&_strong]:text-background">
            <span>{t("assets")} <strong>{formatMoney(accounts.base_assets_minor, accounts.base_currency, language)}</strong></span>
            <span>{t("receivables")} <strong>{formatMoney(accounts.base_receivables_minor, accounts.base_currency, language)}</strong></span>
            <span>{t("liabilities")} <strong>−{formatMoney(accounts.base_liabilities_minor, accounts.base_currency, language)}</strong></span>
          </div>
          {#if accounts.foreign_balances.length > 0}
            <div class="mt-4 flex flex-wrap gap-2">
              <p class="w-full text-xs text-background/70">{t("unconvertedBalances")}</p>
              {#each accounts.foreign_balances as row (row.currency)}
                <span class="inline-flex items-baseline gap-2 rounded-full bg-background/10 px-3 py-1.5 font-mono text-xs">
                  {formatMoneyWithCode(row.balance_minor, row.currency, language)}
                  <small class="text-background/70">{row.account_count} {t("accountsLower")}</small>
                </span>
              {/each}
            </div>
          {/if}
        {:else}
          <p class="mt-auto max-w-xl text-background/70">{t("historyUnavailableDetail")}</p>
        {/if}
      </Card.Content>
    </Card.Root>

    <Card.Root class="min-h-[22rem]">
      <Card.Header>
        <Card.Title>{t("cashFlow")}</Card.Title>
        <Card.Description>{t("cashFlowDescription")}</Card.Description>
      </Card.Header>
      <Card.Content>
        <dl class="m-0 grid [&>div]:flex [&>div]:items-baseline [&>div]:justify-between [&>div]:gap-4 [&>div]:border-b [&>div]:py-3 [&_dt]:text-xs [&_dt]:text-muted-foreground [&_dd]:m-0 [&_dd]:text-right [&_dd]:font-mono [&_dd]:text-sm [&_dd]:font-semibold">
          <div><dt>{t("income")}</dt><dd>{formatMoney(cashFlow.income_minor, cashFlow.base_currency, language)}</dd></div>
          <div><dt>{t("expense")}</dt><dd>{formatMoney(cashFlow.expense_minor, cashFlow.base_currency, language)}</dd></div>
          <div class="border-b-0! text-foreground [&_dd]:text-xl [&_dd]:tracking-tight"><dt>{t("net")}</dt><dd>{formatMoney(cashFlow.net_minor, cashFlow.base_currency, language)}</dd></div>
        </dl>
        {#if !cashFlow.conversion_complete}
          <div class="mt-4 grid gap-1 rounded-md bg-muted p-3 text-xs text-muted-foreground [&>p]:m-0 [&>span]:m-0">
            <Badge variant="outline">{t("partial")}</Badge>
            <p>{t("partialConversionNote")}</p>
            {#each cashFlow.unconverted as row (row.currency)}
              <span>
                +{formatMoneyWithCode(row.income_minor, row.currency, language)} / −{formatMoneyWithCode(row.expense_minor, row.currency, language)}
              </span>
            {/each}
          </div>
        {/if}
      </Card.Content>
    </Card.Root>
  </div>

  <Card.Root>
    <Card.Content class="py-2">
      <CashFlowChart
        buckets={weeks}
        currency={cashFlow.base_currency}
        {language}
        {t}
      />
    </Card.Content>
  </Card.Root>

  <div class="grid items-start gap-4 lg:grid-cols-[minmax(0,1.08fr)_minmax(18rem,0.92fr)]">
    <Card.Root>
      <Card.Header>
        <Card.Title>{t("accountsTitle")}</Card.Title>
        <Card.Description>{t("accountsDescription")}</Card.Description>
      </Card.Header>
      <Card.Content>
        {#if !accounts.available}
          <p class="m-0 text-xs text-muted-foreground">{t("historyUnavailableDetail")}</p>
        {:else if accounts.groups.length === 0}
          <p class="m-0 text-xs text-muted-foreground">{t("noAccounts")}</p>
        {:else}
          <div class="grid gap-4">
            {#each accounts.groups as group (group.name)}
              <section>
                <h3 class="mb-1 font-mono text-xs uppercase tracking-wider text-muted-foreground">{group.name}</h3>
                {#each group.accounts as account (account.id)}
                  <div class="flex items-center justify-between gap-4 border-b py-3 last:border-b-0 max-[45rem]:items-start">
                    <div class="grid min-w-0">
                      <strong class="break-words">{account.name}</strong>
                      <span class="text-xs text-muted-foreground">{accountTypeLabel(account.type)} · {account.currency}</span>
                    </div>
                    <b class="shrink-0 font-mono text-xs max-[45rem]:max-w-[46%] max-[45rem]:break-words max-[45rem]:text-right">{formatMoney(account.signed_balance_minor, account.currency, language)}</b>
                  </div>
                {/each}
              </section>
            {/each}
          </div>
        {/if}
      </Card.Content>
    </Card.Root>

    <Card.Root>
      <Card.Header>
        <Card.Title>{t("budgetProgress")}</Card.Title>
        <Card.Description>{t("budgetDescription")}</Card.Description>
      </Card.Header>
      <Card.Content>
        {#if budgets.length === 0}
          <p class="m-0 text-xs text-muted-foreground">{t("noBudgets")}</p>
        {:else}
          <div class="grid gap-4">
            {#each budgets as budget (budget.id)}
              <div class="grid gap-2 border-b pb-3 last:border-b-0 last:pb-0" data-status={budget.status}>
                <div class="flex items-start justify-between gap-4">
                  <div class="grid"><strong>{budget.name}</strong><span class="text-xs text-muted-foreground">{budget.group || budget.category}</span></div>
                  <b class="font-mono text-xs">{formatPercent(budget.ratio * 100, language)}</b>
                </div>
                <progress
                  class={`h-2 w-full overflow-hidden rounded-full border-0 bg-muted ${budget.status === "over" ? "accent-destructive" : budget.status === "watch" ? "accent-chart-4" : budget.status === "partial" ? "accent-muted-foreground" : "accent-primary"}`}
                  aria-label={`${budget.name} · ${t("budgetProgress")}`}
                  max="100"
                  value={Math.min(100, budget.ratio * 100)}
                >
                  {formatPercent(budget.ratio * 100, language)}
                </progress>
                <p class="m-0 text-xs text-muted-foreground">
                  {formatMoney(budget.spent_minor, budget.currency, language)} / {formatMoney(budget.limit_minor, budget.currency, language)}
                  {#if !budget.conversion_complete} · {t("partial")}{/if}
                </p>
                {#if budget.native_spending.length > 0}
                  <div class="grid gap-1 border-l-2 border-input pl-2 text-xs text-muted-foreground">
                    {#each budget.native_spending as native (native.currency)}
                      <span>
                        {formatMoneyWithCode(native.expense_minor, native.currency, language)} · {t("excludedFromProgress")}
                      </span>
                    {/each}
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </Card.Content>
    </Card.Root>
  </div>
</section>
