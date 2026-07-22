import { useEffect, useState } from 'react';
import { getSubscriptionPlans, isApiError, isTimeoutError } from '../api/client';
import type { AcquiringPayment, ClientProfile, Subscription, SubscriptionPlan } from '../api/types';
import { ContentText } from './ContentText';
import { useContentText } from '../content/ContentContext';
import { isTrialEligible } from '../utils/subscription';

export const LEGAL_DOCUMENT_URLS = {
  privacy: 'https://bloomclub.ru/privacy/',
  agreement: 'https://bloomclub.ru/terms/',
  personalDataConsent: 'https://bloomclub.ru/personal-data-consent/',
  offer: 'https://bloomclub.ru/offer/',
} as const;

interface SubscriptionPaymentCardProps {
  profile: ClientProfile | null;
  subscription: Subscription | null;
  isCreatingPayment: boolean;
  onCreatePayment: (email: string, subscriptionPlanId: number) => Promise<AcquiringPayment | null>;
  onActivateTrial: () => Promise<Subscription>;
  onPlanLoaded?: (plan: SubscriptionPlan | null) => void;
}

function getTrialErrorMessage(error: unknown): string {
  if (isTimeoutError(error)) return 'Загрузка заняла слишком много времени. Попробуйте ещё раз.';
  if (isApiError(error) && error.status === 409) return 'У вас уже есть активный доступ';
  if (isApiError(error) && [400, 403, 422].includes(error.status || 0)) return 'Пробный период уже использован';
  return 'Не удалось активировать тестовый период. Попробуйте ещё раз.';
}

export function SubscriptionPaymentCard({
  profile,
  subscription,
  isCreatingPayment,
  onCreatePayment,
  onActivateTrial,
  onPlanLoaded,
}: SubscriptionPaymentCardProps) {
  const [isActivatingTrial, setIsActivatingTrial] = useState(false);
  const [localError, setLocalError] = useState('');
  const [receiptEmail, setReceiptEmail] = useState(String(profile?.contact_email || profile?.email || ''));
  const [acceptedOffer, setAcceptedOffer] = useState(false);
  const [plan, setPlan] = useState<SubscriptionPlan | null>(null);
  const [planLoadError, setPlanLoadError] = useState('');
  const trialAvailable = isTrialEligible(profile, subscription);
  const priceLabel = plan ? Number(plan.price).toLocaleString('ru-RU', { maximumFractionDigits: 2 }) : '';
  const trialCta = useContentText('subscription.trial.cta', 'Подключить пробный период 15 дней');

  useEffect(() => {
    setReceiptEmail(String(profile?.contact_email || profile?.email || ''));
  }, [profile?.contact_email, profile?.email]);

  useEffect(() => {
    let cancelled = false;
    void getSubscriptionPlans()
      .then((plans) => {
        if (cancelled) return;
        const activePlan = plans.find((item) => item.code === 'monthly') || plans[0] || null;
        setPlan(activePlan);
        setPlanLoadError(activePlan ? '' : 'Активный тариф подписки не найден.');
        onPlanLoaded?.(activePlan);
      })
      .catch(() => {
        if (cancelled) return;
        setPlanLoadError('Не удалось загрузить актуальную стоимость подписки.');
        onPlanLoaded?.(null);
      });
    return () => { cancelled = true; };
  }, [onPlanLoaded]);

  async function handleTrial() {
    setIsActivatingTrial(true);
    setLocalError('');
    try {
      await onActivateTrial();
    } catch (error) {
      setLocalError(getTrialErrorMessage(error));
    } finally {
      setIsActivatingTrial(false);
    }
  }

  async function handlePayment() {
    setLocalError('');
    if (!receiptEmail.includes('@')) {
      setLocalError('Укажите email, на который Точка отправит чек.');
      return;
    }
    if (!acceptedOffer) {
      setLocalError('Подтвердите согласие с условиями оферты.');
      return;
    }
    if (!plan) {
      setLocalError(planLoadError || 'Стоимость подписки ещё загружается.');
      return;
    }

    try {
      const payment = await onCreatePayment(receiptEmail, plan.id);
      if (!payment?.payment_url) throw new Error('Payment URL is missing');
      sessionStorage.setItem('bloom.pendingPaymentId', payment.payment_id);
      window.location.assign(String(payment.payment_url));
    } catch {
      setLocalError('Не удалось создать оплату. Попробуйте ещё раз.');
    }
  }

  return (
    <div className="subscription-card">
      <ContentText as="p" className="eyebrow" textKey="subscription.eyebrow" fallback="Подписка Bloom Club" />
      <h1>{plan ? `${priceLabel} ₽ / ${plan.duration_days} дней` : 'Загружаем стоимость…'}</h1>
      <ContentText as="p" textKey="subscription.description" fallback="Доступ на 1 месяц к клубным привилегиям у партнёров Bloom Club. Автопродление не подключено, продление выполняется вручную." multiline />
      {trialAvailable ? (
        <button className="button button--primary" type="button" onClick={() => void handleTrial()} disabled={isActivatingTrial}>
          {isActivatingTrial ? 'Активируем…' : trialCta}
        </button>
      ) : null}
      <label className="payment-email-field">
        <span>Email для отправки чека</span>
        <input type="email" value={receiptEmail} onChange={(event) => setReceiptEmail(event.target.value)} autoComplete="email" placeholder="name@example.com" />
      </label>
      <label className="payment-consent">
        <input type="checkbox" checked={acceptedOffer} onChange={(event) => setAcceptedOffer(event.target.checked)} />
        <span>Я принимаю условия <a href={LEGAL_DOCUMENT_URLS.offer} target="_blank" rel="noopener noreferrer">оферты</a> и условия возврата.</span>
      </label>
      <button className="button button--primary" type="button" onClick={() => void handlePayment()} disabled={isCreatingPayment || !plan}>
        {isCreatingPayment ? 'Создаём оплату…' : plan ? `Оплатить подписку — ${priceLabel} ₽` : 'Стоимость загружается…'}
      </button>
      <small>На странице Точки можно выбрать СБП или банковскую карту.</small>
      {planLoadError ? <p className="error-text">{planLoadError}</p> : null}
      {localError ? <p className="error-text">{localError}</p> : null}
    </div>
  );
}
