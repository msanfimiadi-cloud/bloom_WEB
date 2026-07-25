import type { Partner } from '../api/types';
import { getPartnerCategories, sortPartnersForCatalog } from './partnerDisplay';

function normalizeCategoryKey(category: string): string {
  return category.replace(/\s+/g, ' ').trim().toLocaleLowerCase('ru-RU');
}

export function buildCatalogCategories(partners: Partner[] | null | undefined): string[] {
  const safePartners = sortPartnersForCatalog(partners);
  const categories = safePartners.flatMap(getPartnerCategories);
  const uniqueCategories = new Map<string, string>();

  categories.forEach((category) => {
    const displayName = category.replace(/\s+/g, ' ').trim();
    const key = normalizeCategoryKey(displayName);
    if (key && !uniqueCategories.has(key)) {
      uniqueCategories.set(key, displayName);
    }
  });

  return ['Все', ...Array.from(uniqueCategories.values()).sort((a, b) => a.localeCompare(b, 'ru'))];
}

export function filterPartnersByCategory(partners: Partner[] | null | undefined, category: string): Partner[] {
  const safePartners = sortPartnersForCatalog(partners);
  const selectedCategoryKey = normalizeCategoryKey(category);
  if (selectedCategoryKey === normalizeCategoryKey('Все')) {
    return safePartners;
  }

  return safePartners.filter((partner) =>
    getPartnerCategories(partner).some(
      (partnerCategory) => normalizeCategoryKey(partnerCategory) === selectedCategoryKey,
    ),
  );
}
