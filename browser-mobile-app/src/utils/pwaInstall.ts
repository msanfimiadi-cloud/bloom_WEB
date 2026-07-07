import { useCallback, useEffect, useMemo, useState } from 'react';

type BeforeInstallPromptOutcome = 'accepted' | 'dismissed';

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: BeforeInstallPromptOutcome; platform: string }>;
};

type AddToHomeScreenMode = 'native' | 'ios' | 'telegram' | 'unsupported';

export interface AddToHomeScreenState {
  canShow: boolean;
  isStandalone: boolean;
  mode: AddToHomeScreenMode;
  showIosInstructions: boolean;
  addToHomeScreen: () => Promise<void>;
  closeIosInstructions: () => void;
  openInSystemBrowser: () => void;
}

function getUserAgent(): string {
  return typeof navigator === 'undefined' ? '' : navigator.userAgent || '';
}

export function isStandaloneDisplayMode(): boolean {
  if (typeof window === 'undefined') {
    return false;
  }

  const iosStandalone = Boolean((navigator as Navigator & { standalone?: boolean }).standalone);
  const displayModeStandalone = window.matchMedia?.('(display-mode: standalone)').matches ?? false;
  const displayModeFullscreen = window.matchMedia?.('(display-mode: fullscreen)').matches ?? false;
  const displayModeMinimalUi = window.matchMedia?.('(display-mode: minimal-ui)').matches ?? false;

  return iosStandalone || displayModeStandalone || displayModeFullscreen || displayModeMinimalUi;
}

function isIosLikeBrowser(): boolean {
  const userAgent = getUserAgent();
  const platform = navigator.platform || '';
  const maxTouchPoints = navigator.maxTouchPoints || 0;

  return /iphone|ipad|ipod/i.test(userAgent) || (platform === 'MacIntel' && maxTouchPoints > 1);
}

function isTelegramInAppBrowser(): boolean {
  if (typeof window === 'undefined') {
    return false;
  }

  const userAgent = getUserAgent();
  return /telegram|tgwebview/i.test(userAgent) || Boolean(window.Telegram?.WebApp || window.TelegramWebviewProxy || window.TelegramGameProxy);
}

function openCurrentUrlInSystemBrowser(): void {
  if (typeof window === 'undefined') {
    return;
  }

  const currentUrl = window.location.href;
  const opened = window.open(currentUrl, '_blank', 'noopener,noreferrer');
  if (!opened) {
    window.location.href = currentUrl;
  }
}

export function useAddToHomeScreen(): AddToHomeScreenState {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isStandalone, setIsStandalone] = useState(() => isStandaloneDisplayMode());
  const [showIosInstructions, setShowIosInstructions] = useState(false);

  useEffect(() => {
    const updateStandaloneState = () => setIsStandalone(isStandaloneDisplayMode());
    const standaloneQuery = window.matchMedia?.('(display-mode: standalone)');

    updateStandaloneState();
    standaloneQuery?.addEventListener?.('change', updateStandaloneState);
    window.addEventListener('appinstalled', updateStandaloneState);

    return () => {
      standaloneQuery?.removeEventListener?.('change', updateStandaloneState);
      window.removeEventListener('appinstalled', updateStandaloneState);
    };
  }, []);

  useEffect(() => {
    const handleBeforeInstallPrompt = (event: Event) => {
      event.preventDefault();
      setDeferredPrompt(event as BeforeInstallPromptEvent);
    };

    const handleAppInstalled = () => {
      setDeferredPrompt(null);
      setShowIosInstructions(false);
      setIsStandalone(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const mode = useMemo<AddToHomeScreenMode>(() => {
    if (isTelegramInAppBrowser()) {
      return 'telegram';
    }

    if (deferredPrompt) {
      return 'native';
    }

    if (isIosLikeBrowser()) {
      return 'ios';
    }

    return 'unsupported';
  }, [deferredPrompt]);

  const addToHomeScreen = useCallback(async () => {
    if (mode === 'native' && deferredPrompt) {
      await deferredPrompt.prompt();
      const choice = await deferredPrompt.userChoice.catch(() => null);
      if (choice?.outcome === 'accepted') {
        setIsStandalone(true);
      }
      setDeferredPrompt(null);
      return;
    }

    if (mode === 'ios' || mode === 'unsupported') {
      setShowIosInstructions(true);
    }
  }, [deferredPrompt, mode]);

  return {
    canShow: !isStandalone && mode !== 'unsupported',
    isStandalone,
    mode,
    showIosInstructions,
    addToHomeScreen,
    closeIosInstructions: () => setShowIosInstructions(false),
    openInSystemBrowser: openCurrentUrlInSystemBrowser,
  };
}
