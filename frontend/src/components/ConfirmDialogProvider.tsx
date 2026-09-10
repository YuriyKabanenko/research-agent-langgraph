import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from "@mui/material";

export interface ConfirmOptions {
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
}

type ConfirmFn = (options: ConfirmOptions) => Promise<boolean>;

const ConfirmDialogContext = createContext<ConfirmFn | null>(null);

interface PendingConfirm extends ConfirmOptions {
  resolve: (value: boolean) => void;
}

// App-wide replacement for window.confirm: renders a themed MUI Dialog instead of the
// native browser prompt, and resolves a promise so call sites keep the simple
// `if (!(await confirm({...}))) return;` shape they'd have had with window.confirm.
export function ConfirmDialogProvider({ children }: { children: ReactNode }) {
  const [pending, setPending] = useState<PendingConfirm | null>(null);

  const confirm = useCallback<ConfirmFn>((options) => {
    return new Promise<boolean>((resolve) => {
      setPending({ ...options, resolve });
    });
  }, []);

  function close(result: boolean) {
    pending?.resolve(result);
    setPending(null);
  }

  const value = useMemo(() => confirm, [confirm]);

  return (
    <ConfirmDialogContext.Provider value={value}>
      {children}
      <Dialog
        open={pending != null}
        onClose={() => close(false)}
        maxWidth="xs"
        fullWidth
        slotProps={{ paper: { sx: { p: 0.5 } } }}
      >
        <DialogTitle sx={{ fontWeight: 700 }}>{pending?.title}</DialogTitle>
        {pending?.description && (
          <DialogContent>
            <DialogContentText>{pending.description}</DialogContentText>
          </DialogContent>
        )}
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={() => close(false)} color="inherit">
            {pending?.cancelText ?? "Cancel"}
          </Button>
          <Button
            onClick={() => close(true)}
            variant="contained"
            color={pending?.danger ? "error" : "primary"}
            autoFocus
          >
            {pending?.confirmText ?? "Confirm"}
          </Button>
        </DialogActions>
      </Dialog>
    </ConfirmDialogContext.Provider>
  );
}

export function useConfirm(): ConfirmFn {
  const ctx = useContext(ConfirmDialogContext);
  if (!ctx) {
    throw new Error("useConfirm must be used within ConfirmDialogProvider");
  }
  return ctx;
}
