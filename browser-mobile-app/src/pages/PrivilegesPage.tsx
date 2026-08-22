import type { Offer, Verification } from '../api/types';
import { EmptyState } from '../components/EmptyState';
import { ContentText } from '../components/ContentText';
import { useContentText } from '../content/ContentContext';
import { formatDate, formatMoney } from '../utils/format';
import { getOfferPrices, getOfferTitle, getPartnerName, getVerificationCode } from '../utils/partnerDisplay';
import { toText } from '../utils/text';
import { useEffect, useMemo, useState } from 'react';

interface PrivilegesPageProps {
  verifications?: Verification[] | null;
  emptyTitle?: string;
  emptyDescription?: string;
}


function mergeDefinedPriceSource(verification: Verification): Offer | Verification {
  const merged: Record<string, unknown> = { ...(verification.offer || {}) };

  Object.entries(verification).forEach(([key, value]) => {
    if (value !== undefined && key !== 'offer') {
      merged[key] = value;
    }
  });

  return merged as Offer | Verification;
}

function statusLabel(verification: Verification, currentTime: number): string {
  const effectiveStatus = verificationFilter(verification, currentTime);

  if (effectiveStatus === 'used') {
    return 'Использована';
  }

  if (effectiveStatus === 'expired') {
    return 'Истекла';
  }

  return 'Активна';
}

type VerificationFilter = 'active' | 'used' | 'expired';

function verificationFilter(verification: Verification, currentTime: number): VerificationFilter {
  const normalized = toText(verification.status).toLowerCase();
  if (normalized === 'confirmed' || normalized === 'used') return 'used';
  if (normalized === 'expired') return 'expired';

  const expiresAt = toText(verification.expires_at || verification.valid_until);
  const expirationTime = expiresAt ? Date.parse(expiresAt) : Number.NaN;
  if (Number.isFinite(expirationTime) && expirationTime <= currentTime) return 'expired';

  return 'active';
}

export function PrivilegesPage({ verifications, emptyTitle, emptyDescription }: PrivilegesPageProps) {
  const safeVerifications = Array.isArray(verifications) ? verifications : [];
  const [activeFilter, setActiveFilter] = useState<VerificationFilter>('active');
  const [currentTime, setCurrentTime] = useState(() => Date.now());

  useEffect(() => {
    const timer = window.setInterval(() => setCurrentTime(Date.now()), 30_000);
    return () => window.clearInterval(timer);
  }, []);

  const counts = useMemo(() => safeVerifications.reduce<Record<VerificationFilter, number>>((result, verification) => {
    result[verificationFilter(verification, currentTime)] += 1;
    return result;
  }, { active: 0, used: 0, expired: 0 }), [currentTime, safeVerifications]);
  const visibleVerifications = useMemo(
    () => safeVerifications.filter((verification) => verificationFilter(verification, currentTime) === activeFilter),
    [activeFilter, currentTime, safeVerifications],
  );
  const defaultEmptyTitle = useContentText('privileges.empty.title', 'Здесь появятся ваши коды привилегий');
  const defaultEmptyDescription = useContentText('privileges.empty.description', 'Выберите партнёра и получите код на нужную услугу.');

  return (
    <section className="page">
      <div className="page-header">
        <ContentText as="p" className="eyebrow" textKey="privileges.eyebrow" fallback="Мои привилегии" />
        <ContentText as="h1" textKey="privileges.title" fallback="Коды привилегий" />
        <ContentText as="p" textKey="privileges.description" fallback="Здесь сохраняются коды, которые вы получили у партнёров клуба." multiline />
      </div>

      {safeVerifications.length ? (
        <>
          <div className="verification-filters" role="tablist" aria-label="Фильтр кодов привилегий">
            {([
              ['active', 'Активные'],
              ['used', 'Использованные'],
              ['expired', 'Истёкшие'],
            ] as const).map(([filter, label]) => (
              <button
                className={activeFilter === filter ? 'verification-filter verification-filter--active' : 'verification-filter'}
                type="button"
                role="tab"
                aria-selected={activeFilter === filter}
                onClick={() => setActiveFilter(filter)}
                key={filter}
              >
                {label} <span>{counts[filter]}</span>
              </button>
            ))}
          </div>
          {visibleVerifications.length ? <div className="verification-list">
          {visibleVerifications.map((verification, index) => {
            const prices = getOfferPrices(mergeDefinedPriceSource(verification));
            const hasPriceDetails = prices.basePrice !== undefined || prices.hasValidMemberPrice || prices.hasValidSaving;
            const code = getVerificationCode(verification) || 'Код формируется';
            const partnerName = verification.partner
              ? getPartnerName(verification.partner)
              : toText(verification.partner_name, 'Партнёр Bloom Club');
            const offerTitle = verification.offer
              ? getOfferTitle(verification.offer)
              : toText(verification.offer_title, 'Услуга партнёра');

            return (
              <article className="verification-card" key={verification.id ?? index}>
                <div className="verification-card__code">
                  <span>Код привилегии</span>
                  <strong>{code}</strong>
                </div>
                <div>
                  <strong>{partnerName}</strong>
                  <p>{offerTitle}</p>
                  <p>Статус: {statusLabel(verification, currentTime)}</p>
                  <small>Действует до: {formatDate(verification.expires_at || verification.valid_until)}</small>
                  <div className="price-grid price-grid--compact">
                    {prices.basePrice !== undefined ? <span><small>Обычная цена</small>{formatMoney(prices.basePrice)}</span> : null}
                    {prices.hasValidMemberPrice ? <span><small>Цена для участницы</small>{formatMoney(prices.memberPrice)}</span> : null}
                    {prices.hasValidSaving ? <span><small>Экономия</small>{formatMoney(prices.saving)}</span> : null}
                  </div>
                  {!hasPriceDetails ? <small className="verification-card__missing-price">Данные о стоимости для этого старого кода не были сохранены.</small> : null}
                </div>
              </article>
            );
          })}
          </div> : <EmptyState title={`Нет кодов: ${activeFilter === 'active' ? 'активных' : activeFilter === 'used' ? 'использованных' : 'истёкших'}`} description="Выберите другую вкладку." />}
        </>
      ) : (
        <EmptyState
          title={emptyTitle || defaultEmptyTitle}
          description={emptyDescription || defaultEmptyDescription}
        />
      )}
    </section>
  );
}
