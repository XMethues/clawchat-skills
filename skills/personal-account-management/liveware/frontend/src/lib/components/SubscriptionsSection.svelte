<script lang="ts">
  import CalendarClockIcon from "@lucide/svelte/icons/calendar-clock";
  import { Badge } from "$lib/components/ui/badge";
  import * as Card from "$lib/components/ui/card";
  import { formatDate, formatInteger, formatMoneyWithCode } from "$lib/format";
  import type { TranslationKey } from "$lib/i18n";
  import { summarizeSubscriptions } from "$lib/selectors";
  import type { BookResponse, Language, SubscriptionView } from "$lib/types";

  type Props = {
    book: BookResponse;
    language: Language;
    t: (key: TranslationKey) => string;
  };

  let { book, language, t }: Props = $props();

  const summary = $derived(summarizeSubscriptions(book));
  const accountNames = $derived(new Map(
    book.account_snapshot.accounts.map((account) => [account.id, account.name]),
  ));

  function statusKey(status: SubscriptionView["status"]): TranslationKey {
    if (status === "observed") return "subscriptionObserved";
    if (status === "expected") return "subscriptionExpected";
    if (status === "unexpected") return "subscriptionUnexpected";
    if (status === "mismatch") return "subscriptionMismatch";
    return "subscriptionNotDue";
  }

  function cadenceKey(cadence: string): TranslationKey {
    if (cadence === "custom") return "cadenceCustom";
    if (cadence === "weekly") return "cadenceWeekly";
    if (cadence === "quarterly") return "cadenceQuarterly";
    if (cadence === "yearly") return "cadenceYearly";
    return "cadenceMonthly";
  }
</script>

<section class="grid gap-4" aria-labelledby="subscriptions-title">
  <div class="flex items-end justify-between gap-4 max-[45rem]:flex-col max-[45rem]:items-start">
    <div>
      <p class="mb-0.5 font-mono text-xs font-semibold uppercase tracking-widest text-muted-foreground">{formatInteger(summary.rows.length, language)} {t("subscriptionsLower")}</p>
      <h2 id="subscriptions-title" class="text-3xl font-semibold tracking-tight sm:text-4xl">{t("subscriptionsTitle")}</h2>
      <p class="mt-1 max-w-2xl text-muted-foreground">{t("subscriptionsDescription")}</p>
    </div>
  </div>

  {#if summary.totals.length > 0}
    <div class="grid grid-cols-[repeat(auto-fit,minmax(13rem,1fr))] gap-3" aria-label={t("selectedMonthTotals")}>
      {#each summary.totals as total (total.currency)}
        <Card.Root size="sm">
          <Card.Content class="grid gap-1">
            <span class="text-xs text-muted-foreground">{t("selectedMonthTotals")}</span>
            <div class="grid grid-cols-[1fr_auto] items-baseline gap-2">
              <span class="text-xs text-muted-foreground">{t("subscriptionExpected")}</span>
              <strong class="text-right text-base font-semibold tracking-tight break-words">{formatMoneyWithCode(total.expected_minor, total.currency, language)}</strong>
            </div>
            <div class="grid grid-cols-[1fr_auto] items-baseline gap-2">
              <span class="text-xs text-muted-foreground">{t("subscriptionObserved")}</span>
              <strong class="text-right text-base font-semibold tracking-tight break-words">{formatMoneyWithCode(total.observed_minor, total.currency, language)}</strong>
            </div>
            <small class="text-xs text-muted-foreground">{total.subscription_count} {t("subscriptionsLower")}</small>
          </Card.Content>
        </Card.Root>
      {/each}
    </div>
  {/if}

  {#if summary.rows.length === 0}
    <Card.Root>
      <Card.Content class="grid min-h-56 place-items-center text-center">
        <div>
          <h3 class="text-xl font-semibold tracking-tight">{t("noSubscriptions")}</h3>
          <p class="mx-auto mt-2 max-w-xl text-muted-foreground">{t("noSubscriptionsDescription")}</p>
        </div>
      </Card.Content>
    </Card.Root>
  {:else}
    <div class="grid gap-3">
      {#each summary.rows as subscription (subscription.id)}
        <Card.Root class="min-h-80 w-full data-[status=mismatch]:border-destructive/50" data-status={subscription.status}>
          <Card.Header>
            <div class="flex min-w-0 items-start justify-between gap-3">
              <div class="min-w-0">
                <Card.Title class="break-words">{subscription.name}</Card.Title>
                <Card.Description class="break-words">
                  {subscription.description || t(cadenceKey(subscription.cadence))}
                </Card.Description>
              </div>
              <Badge variant={subscription.status === "mismatch" ? "destructive" : "outline"}>
                {t(statusKey(subscription.status))}
              </Badge>
            </div>
          </Card.Header>
          <Card.Content class="flex flex-1 flex-col gap-4">
            <strong class="text-3xl font-semibold tracking-tighter break-words sm:text-4xl">
              {formatMoneyWithCode(subscription.amount_minor, subscription.currency, language)}
            </strong>
            <dl class="m-0 grid gap-2">
              <div class="grid grid-cols-[minmax(7rem,0.45fr)_minmax(0,1fr)] gap-3 border-b pb-2 max-[45rem]:grid-cols-1 max-[45rem]:gap-0.5">
                <dt class="text-xs text-muted-foreground">{t("cadence")}</dt>
                <dd class="m-0 text-right text-xs font-semibold break-words max-[45rem]:text-left">{t(cadenceKey(subscription.cadence))}</dd>
              </div>
              <div class="grid grid-cols-[minmax(7rem,0.45fr)_minmax(0,1fr)] gap-3 border-b pb-2 max-[45rem]:grid-cols-1 max-[45rem]:gap-0.5">
                <dt class="text-xs text-muted-foreground">{t("nextBilling")}</dt>
                <dd class="m-0 text-right text-xs font-semibold break-words max-[45rem]:text-left">{formatDate(subscription.next_billing_date, language)}</dd>
              </div>
              <div class="grid grid-cols-[minmax(7rem,0.45fr)_minmax(0,1fr)] gap-3 border-b pb-2 max-[45rem]:grid-cols-1 max-[45rem]:gap-0.5">
                <dt class="text-xs text-muted-foreground">{t("paymentAccount")}</dt>
                <dd class="m-0 text-right text-xs font-semibold break-words max-[45rem]:text-left">{accountNames.get(subscription.payment_account_id) ?? t("unknownAccount")}</dd>
              </div>
            </dl>
            <div class="mt-auto flex items-start gap-3 rounded-md bg-muted p-3">
              <CalendarClockIcon class="size-4 shrink-0 text-primary" aria-hidden="true" />
              <div>
                {#if subscription.expected_dates.length > 0}
                  <p class="text-xs font-semibold">{t("expectedThisMonth")}</p>
                  <span class="block text-xs text-muted-foreground">{subscription.expected_dates.map((date) => formatDate(date, language)).join(" · ")}</span>
                {:else}
                  <p class="text-xs font-semibold">{t("notExpectedThisMonth")}</p>
                {/if}
                {#if subscription.observed_count > 0}
                  <small class="block text-xs text-muted-foreground">{subscription.observed_count} {t("observedCharges")}</small>
                  <ul class="mt-1 grid list-none gap-1 p-0">
                    {#each subscription.observed_charges as charge (charge.id)}
                      <li class="flex min-w-0 items-baseline justify-between gap-3">
                        <span class="min-w-0 text-xs text-muted-foreground break-words">{formatDate(charge.date, language)}</span>
                        <strong class="min-w-0 text-right font-mono text-xs break-words">{formatMoneyWithCode(charge.amount_minor, charge.currency, language)}</strong>
                      </li>
                    {/each}
                  </ul>
                {/if}
              </div>
            </div>
          </Card.Content>
        </Card.Root>
      {/each}
    </div>
  {/if}
</section>
