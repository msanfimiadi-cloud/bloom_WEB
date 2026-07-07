import type React from 'react';
import { useMemo, useState } from 'react';
import {
  isApiError,
  linkVkLoginCode,
  storeAuthTokenFromResponse,
} from '../api/client';
import type { LinkingConfirmResponse } from '../api/types';
import { toText } from '../utils/text';

type LinkingStep = 'question' | 'vkCode' | 'success';
type TextChangeEvent = { target?: { value?: string } | null; currentTarget?: { value?: string } | null } | null | undefined;

function readChangeValue(event: TextChangeEvent): string {
  return event?.currentTarget?.value ?? event?.target?.value ?? '';
}

interface AccountLinkingOnboardingProps {
  onDismiss: () => void;
  onLinked: () => Promise<void> | void;
}

function getSafeDetailText(detail: unknown): string {
  if (detail === undefined || detail === null) {
    return '';
  }

  return (toText(detail) || JSON.stringify(detail)).toLowerCase();
}

function getConfirmErrorMessage(error: unknown): string {
  const detail = isApiError(error) ? error.detail : undefined;
  const detailText = getSafeDetailText(detail);

  if (detailText.includes('temporary_profile_has_activity')) {
    return 'Этот Telegram-профиль уже использовался. Напишите администратору для объединения.';
  }

  if (detailText.includes('expired')) {
    return 'Срок действия кода истёк. Запросите новый код и попробуйте ещё раз.';
  }

  if (detailText.includes('invalid') || detailText.includes('code')) {
    return 'Неверный код. Проверьте код и попробуйте ещё раз.';
  }

  return 'Не удалось подтвердить привязку. Проверьте код и попробуйте ещё раз.';
}

export function AccountLinkingOnboarding({ onDismiss, onLinked }: AccountLinkingOnboardingProps) {
  const [step, setStep] = useState<LinkingStep>('question');
  const [code, setCode] = useState('');
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canSubmitCode = useMemo(() => code.trim().length > 0, [code]);

  async function submitCode() {
    if (!canSubmitCode || isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setMessage('');

    try {
      const response: LinkingConfirmResponse = await linkVkLoginCode(code.trim());
      storeAuthTokenFromResponse(response);
      await onLinked();
      setStep('success');
      setMessage('Профиль привязан');
    } catch (error) {
      setMessage(getConfirmErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="linking-modal" role="dialog" aria-modal="true" aria-labelledby="linking-title">
      <div className="linking-modal__card">
        {step === 'question' ? (
          <>
            <p className="eyebrow">Профиль</p>
            <h2 id="linking-title">Вы уже пользовались Bloom Club во ВКонтакте?</h2>
            <p>Мы можем привязать ваш Telegram к существующему профилю, чтобы сохранить доступ, тестовый период и привилегии.</p>
            <div className="linking-modal__actions">
              <button className="button button--primary" type="button" onClick={() => setStep('vkCode')}>
                Да, привязать профиль
              </button>
              <button className="button button--ghost" type="button" onClick={onDismiss}>
                Нет, продолжить
              </button>
            </div>
          </>
        ) : null}

        {step === 'vkCode' ? (
          <form
            className="linking-modal__form"
            onSubmit={(event: React.FormEvent<HTMLFormElement>) => {
              event.preventDefault();
              void submitCode();
            }}
          >
            <p className="eyebrow">Подтверждение</p>
            <h2 id="linking-title">Введите код из VK-бота</h2>
            <input value={code} onChange={(event: React.ChangeEvent<HTMLInputElement>) => setCode(readChangeValue(event))} placeholder="BC-XXXXXX" />
            {message ? <p className="error-text">{message}</p> : null}
            <div className="linking-modal__actions">
              <button className="button button--primary" type="submit" disabled={!canSubmitCode || isSubmitting}>
                Подтвердить
              </button>
              <button className="button button--ghost" type="button" onClick={() => setStep('question')}>
                Назад
              </button>
            </div>
          </form>
        ) : null}

        {step === 'success' ? (
          <>
            <p className="eyebrow">Готово</p>
            <h2 id="linking-title">Профиль привязан</h2>
            <p className="success-text">{message || 'Профиль привязан'}</p>
            <button className="button button--primary" type="button" onClick={onDismiss}>
              Продолжить
            </button>
          </>
        ) : null}
      </div>
    </div>
  );
}
