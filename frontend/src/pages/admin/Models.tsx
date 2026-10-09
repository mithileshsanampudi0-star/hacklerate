import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  Brain,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Activity,
  BarChart3,
  Calendar,
  Sparkles,
} from "lucide-react";
import { api, errorMessage, useApi } from "../../api/client";
import type { ModelMetadata } from "../../api/types";

export default function AdminModels() {
  const queryClient = useQueryClient();
  const { data: models, isLoading, error } = useApi<ModelMetadata[]>("/admin/models");
  const [retraining, setRetraining] = useState(false);
  const [retrainResult, setRetrainResult] = useState<string | null>(null);
  const [retrainError, setRetrainError] = useState<string | null>(null);

  const handleRetrain = async () => {
    setRetraining(true);
    setRetrainResult(null);
    setRetrainError(null);
    try {
      const res = await api.post<{ message: string; result: any }>("/admin/models/retrain");
      setRetrainResult(res.data.message || "Model retrained successfully");
      await queryClient.invalidateQueries({ queryKey: ["/admin/models"] });
    } catch (err) {
      setRetrainError(errorMessage(err));
    } finally {
      setRetraining(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
            <Sparkles className="h-3.5 w-3.5" />
            Machine Learning Governance
          </div>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">
            Predictive Models & Governance
          </h1>
          <p className="text-sm text-slate-500">
            Inspect model training metadata and feature weights. Student-facing academic risk scores are calculated
            separately by the rule-based scoring shown on student dashboards.
          </p>
        </div>

        <button
          onClick={handleRetrain}
          disabled={retraining}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 disabled:opacity-60 transition-colors"
        >
          <RefreshCw className={`h-4 w-4 ${retraining ? "animate-spin" : ""}`} />
          {retraining ? "Refreshing Training Metadata..." : "Refresh Training Metadata"}
        </button>
      </div>

      {retrainResult && (
        <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-800 text-sm">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
          <span>{retrainResult}</span>
        </div>
      )}

      {retrainError && (
        <div className="flex items-center gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-rose-800 text-sm">
          <AlertTriangle className="h-5 w-5 text-rose-600 shrink-0" />
          <span>{retrainError}</span>
        </div>
      )}

      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <RefreshCw className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      ) : error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-rose-800">
          Failed to load model metadata: {errorMessage(error)}
        </div>
      ) : (
        <div className="space-y-6">
          {models?.map((model) => {
            const metrics = model.metrics || {};
            const importances = model.feature_importances || {};

            return (
              <div
                key={model.id}
                className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all"
              >
                {/* Model Header Banner */}
                <div className="flex flex-col gap-3 border-b border-slate-100 bg-slate-50/70 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-100 text-indigo-600 font-bold">
                      <Brain className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-base font-bold text-slate-900">{model.model_name}</h2>
                        <span className="rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-700">
                          {model.model_version}
                        </span>
                        {model.is_active && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            Production Active
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">Algorithm: {model.algorithm}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Calendar className="h-3.5 w-3.5 text-slate-400" />
                    <span>Trained: {model.trained_at ? new Date(model.trained_at).toLocaleString() : "Initial"}</span>
                  </div>
                </div>

                <div className="p-6 space-y-6">
                  {/* Evaluation Metrics Grid */}
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
                      <Activity className="h-4 w-4 text-indigo-500" />
                      Recorded Training Metrics
                    </h3>
                    <div className="mb-3 rounded-xl border border-amber-200/70 bg-amber-50/60 p-3 text-xs leading-relaxed text-amber-900">
                      <p className="font-semibold">Interpret these as training metadata, not independent validation.</p>
                      <p className="mt-1 text-amber-800">
                        {model.algorithm.toLowerCase().includes("fallback")
                          ? "Fallback mode displays reference values; it has not measured this dataset's predictive performance."
                          : "The current metrics are calculated on the same records used to fit the model; a separate held-out evaluation is not shown."}
                        {" "}These figures do not measure the separate rule-based score shown to students.
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
                      <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-3 text-center">
                        <span className="text-xs font-medium text-slate-500">Accuracy</span>
                        <p className="mt-1 text-xl font-bold text-slate-900">
                          {metrics.accuracy !== undefined ? `${(metrics.accuracy * 100).toFixed(1)}%` : "N/A"}
                        </p>
                      </div>
                      <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-3 text-center">
                        <span className="text-xs font-medium text-slate-500">Precision</span>
                        <p className="mt-1 text-xl font-bold text-slate-900">
                          {metrics.precision !== undefined ? `${(metrics.precision * 100).toFixed(1)}%` : "N/A"}
                        </p>
                      </div>
                      <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-3 text-center">
                        <span className="text-xs font-medium text-slate-500">Recall</span>
                        <p className="mt-1 text-xl font-bold text-slate-900">
                          {metrics.recall !== undefined ? `${(metrics.recall * 100).toFixed(1)}%` : "N/A"}
                        </p>
                      </div>
                      <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-3 text-center">
                        <span className="text-xs font-medium text-slate-500">F1-Score</span>
                        <p className="mt-1 text-xl font-bold text-slate-900">
                          {metrics.f1 !== undefined ? `${(metrics.f1 * 100).toFixed(1)}%` : "N/A"}
                        </p>
                      </div>
                      <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-3 text-center">
                        <span className="text-xs font-medium text-slate-500">ROC-AUC</span>
                        <p className="mt-1 text-xl font-bold text-indigo-600">
                          {metrics.roc_auc !== undefined ? `${(metrics.roc_auc * 100).toFixed(1)}%` : "N/A"}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Feature Importance Attributions */}
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
                      <BarChart3 className="h-4 w-4 text-indigo-500" />
                      Global Feature Importance
                    </h3>
                    <p className="mb-3 text-xs leading-relaxed text-slate-500">
                      These weights describe the training model overall; they do not explain an individual student's
                      rule-based score or establish that a feature caused an outcome.
                    </p>
                    <div className="space-y-2.5">
                      {Object.entries(importances).map(([feature, weight]) => {
                        const val = typeof weight === "number" ? weight : parseFloat(weight as string) || 0;
                        const pct = Math.round(val * 100);
                        return (
                          <div key={feature} className="space-y-1">
                            <div className="flex justify-between text-xs">
                              <span className="font-medium text-slate-700 capitalize">
                                {feature.replace(/_/g, " ")}
                              </span>
                              <span className="font-semibold text-slate-900">{pct}% weight</span>
                            </div>
                            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                              <div
                                className="h-full rounded-full bg-indigo-500 transition-all duration-500"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Governance & Compliance Notice */}
                  <div className="rounded-xl border border-amber-200/70 bg-amber-50/60 p-4 text-xs text-amber-900 space-y-1">
                    <div className="flex items-center gap-2 font-semibold">
                      <Layers className="h-4 w-4 text-amber-600" />
                      Data scope & responsible interpretation
                    </div>
                    <p className="text-amber-800">
                      Model metadata and student-facing rule-based scores are separate. Review data coverage, training
                      method, and individual student records before using either view to guide support.
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
