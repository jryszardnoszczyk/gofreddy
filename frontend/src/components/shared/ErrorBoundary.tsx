import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertCircle, RotateCcw } from "lucide-react";

interface Props {
  children: ReactNode;
  /** Scoped label for error reporting, e.g. "Canvas" or "Chat" */
  label?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    if (import.meta.env.DEV) {
      console.error(`[ErrorBoundary:${this.props.label ?? "unknown"}]`, error, info.componentStack);
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center gap-3 p-8 text-center">
          <AlertCircle className="h-8 w-8 text-danger" />
          <p className="text-sm text-zinc-400">Something went wrong</p>
          <button
            onClick={this.handleReset}
            className="flex items-center gap-1.5 rounded-lg bg-brand-500/10 px-3 py-1.5 text-xs font-medium text-brand-400 transition-colors hover:bg-brand-500/20"
          >
            <RotateCcw className="h-3 w-3" />
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
