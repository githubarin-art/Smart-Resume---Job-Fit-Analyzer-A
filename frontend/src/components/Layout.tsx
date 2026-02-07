
import React from 'react';
import { Stepper, ANALYZER_STEPS, ASSISTED_STEPS } from './Stepper';
import type { AnalysisMode } from '../services/types';

interface LayoutProps {
    children: React.ReactNode;
    currentStep?: number;
    completedSteps?: number[];
    onReset?: () => void;
    showReset?: boolean;
    onBack?: () => void;
    title?: string;
    mode?: AnalysisMode | null;
}

export const Layout: React.FC<LayoutProps> = ({
    children,
    currentStep = 0,
    completedSteps = [],
    onReset,
    showReset = false,
    onBack,
    mode,
}) => {
    // Use assisted steps if in assisted mode
    const steps = mode === 'assisted' ? ASSISTED_STEPS : ANALYZER_STEPS;

    return (
        <div className="min-h-screen bg-gradient-to-br from-[var(--color-neutral-50)] to-[var(--color-neutral-100)] flex flex-col font-sans text-[var(--color-text-primary)]">
            {/* Accessibility Skip Link */}
            <a href="#main-content" className="skip-link sr-only focus:not-sr-only">
                Skip to main content
            </a>

            {/* Premium Navbar */}
            <header className="sticky top-0 z-50 w-full border-b border-[var(--color-neutral-200)]/50 bg-white/80 backdrop-blur-xl">
                <div className="container h-16 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        {onBack && (
                            <button
                                onClick={onBack}
                                className="p-2 hover:bg-[var(--color-neutral-100)] rounded-xl transition-all hover:scale-105"
                                aria-label="Go back"
                            >
                                <svg className="w-5 h-5 text-[var(--color-neutral-600)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                                </svg>
                            </button>
                        )}

                        <div
                            className="flex items-center gap-3 cursor-pointer group"
                            onClick={onReset}
                            role="button"
                            tabIndex={0}
                            onKeyDown={(e) => e.key === 'Enter' && onReset?.()}
                        >
                            {/* Logo Icon */}
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--color-primary-500)] to-[var(--color-primary-700)] flex items-center justify-center shadow-lg shadow-[var(--color-primary-500)]/20 group-hover:shadow-[var(--color-primary-500)]/40 transition-all group-hover:scale-105">
                                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                            </div>
                            {/* Logo Text */}
                            <div className="flex flex-col">
                                <h1 className="text-lg font-bold tracking-tight bg-gradient-to-r from-[var(--color-primary-600)] to-[var(--color-primary-500)] bg-clip-text text-transparent leading-tight">
                                    ResumeAI
                                </h1>
                                <span className="text-[10px] font-medium text-[var(--color-neutral-400)] uppercase tracking-widest">
                                    Smart Analyzer
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        {showReset && onReset && (
                            <button
                                onClick={onReset}
                                className="flex items-center gap-2 text-sm font-semibold text-[var(--color-primary-600)] hover:text-[var(--color-primary-700)] transition-colors px-4 py-2 rounded-xl hover:bg-[var(--color-primary-50)] border border-transparent hover:border-[var(--color-primary-200)]"
                            >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                                </svg>
                                New Analysis
                            </button>
                        )}
                    </div>
                </div>
            </header>

            {/* Progress Stepper - Context Aware */}
            {currentStep > 1 && (
                <div className="border-b border-[var(--color-border)] bg-[var(--color-surface)] shadow-sm">
                    <div className="container py-2">
                        <Stepper
                            steps={steps}
                            currentStep={currentStep}
                            completedSteps={completedSteps}
                        />
                    </div>
                </div>
            )}

            {/* Main Content */}
            <main
                id="main-content"
                className="flex-1 container py-8 animate-fade-in"
                role="main"
            >
                {children}
            </main>

            {/* Footer */}
            <footer className="border-t border-[var(--color-border)] bg-[var(--color-surface)] py-6 mt-auto">
                <div className="container flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-[var(--color-text-muted)]">
                    <p>© 2026 Smart Resume Analyzer. Open Source.</p>
                    <div className="flex items-center gap-6">
                        <span>Advisory Tool Only</span>
                        <span>Privacy-First (Local Processing)</span>
                    </div>
                </div>
            </footer>
        </div>
    );
};
