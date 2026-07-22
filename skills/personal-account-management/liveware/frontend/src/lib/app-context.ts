import { getContext } from "svelte";
import type { TranslationKey } from "$lib/i18n";
import type { Language } from "$lib/types";

export type DashboardAppContext = {
  language: Language;
  t: (key: TranslationKey) => string;
};

export const DASHBOARD_APP_CONTEXT = Symbol("dashboard-app-context");

export function getDashboardAppContext(): DashboardAppContext {
  return getContext<DashboardAppContext>(DASHBOARD_APP_CONTEXT);
}
