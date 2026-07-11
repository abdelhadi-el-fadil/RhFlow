"use client";

import * as React from "react";
import { createPortal } from "react-dom";

import { cn } from "@/lib/utils";

function useIsMounted() {
  return React.useSyncExternalStore(
    () => () => {}, // no-op subscribe, nothing ever changes after mount
    () => true, // client snapshot: always true once this runs
    () => false, // server snapshot: false during SSR
  );
}

type ComboboxContextValue = {
  items: readonly string[];
  filteredItems: readonly string[];
  query: string;
  setQuery: (value: string) => void;
  isOpen: boolean;
  setIsOpen: (value: boolean) => void;
  selectItem: (value: string) => void;
  anchorRef: React.RefObject<HTMLDivElement | null>;
};

const ComboboxContext = React.createContext<ComboboxContextValue | null>(null);

function useComboboxContext() {
  const context = React.useContext(ComboboxContext);
  if (!context) {
    throw new Error("Combobox components must be used inside <Combobox>");
  }
  return context;
}

type ComboboxProps = {
  items: readonly string[];
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
  className?: string;
};

function Combobox({
  items,
  value,
  defaultValue,
  onValueChange,
  children,
  className,
}: ComboboxProps) {
  const [internalValue, setInternalValue] = React.useState<string>(
    defaultValue ?? "",
  );
  const [isOpen, setIsOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement | null>(null);

  const selectedValue = value ?? internalValue;
  const [query, setQuery] = React.useState(() =>
    selectedValue ? String(selectedValue) : "",
  );

  React.useEffect(() => {
    const handleOutside = (event: MouseEvent) => {
      if (!containerRef.current) {
        return;
      }
      if (!containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleOutside);
    return () => {
      document.removeEventListener("mousedown", handleOutside);
    };
  }, []);

  const filteredItems = React.useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) {
      return items;
    }
    return items.filter((item) => String(item).toLowerCase().includes(needle));
  }, [items, query]);

  const selectItem = (nextValue: string) => {
    if (value === undefined) {
      setInternalValue(nextValue);
    }
    setQuery(String(nextValue));
    setIsOpen(false);
    onValueChange?.(nextValue);
  };

  return (
    <ComboboxContext.Provider
      value={{
        items,
        filteredItems,
        query,
        setQuery,
        isOpen,
        setIsOpen,
        selectItem,
        anchorRef: containerRef,
      }}
    >
      <div ref={containerRef} className={cn("relative", className)}>
        {children}
      </div>
    </ComboboxContext.Provider>
  );
}

function ComboboxInput({
  className,
  onChange,
  onFocus,
  ...props
}: React.ComponentProps<"input">) {
  const { query, setQuery, setIsOpen } = useComboboxContext();

  return (
    <input
      value={query}
      onChange={(event) => {
        setQuery(event.target.value);
        setIsOpen(true);
        onChange?.(event);
      }}
      onFocus={(event) => {
        setIsOpen(true);
        onFocus?.(event);
      }}
      className={cn(
        "h-8 w-full min-w-0 rounded-lg border border-slate-300/90 bg-white px-2.5 py-1 text-base text-slate-800 shadow-md shadow-slate-300/20 transition-all duration-200 outline-none placeholder:text-slate-400 hover:border-sky-400 focus-visible:border-sky-500 focus-visible:ring-2 focus-visible:ring-sky-400/25 disabled:pointer-events-none disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-500 aria-invalid:border-red-500 aria-invalid:ring-2 aria-invalid:ring-red-300 file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-sm file:font-medium md:text-sm",
        className,
      )}
      autoComplete="off"
      {...props}
    />
  );
}

function ComboboxContent({ className, children }: React.ComponentProps<"div">) {
  const { isOpen, anchorRef } = useComboboxContext();
  const mounted = useIsMounted();
  const [rect, setRect] = React.useState<{
    top: number;
    left: number;
    width: number;
  } | null>(null);

  const updatePosition = React.useCallback(() => {
    const anchor = anchorRef.current;
    if (!anchor) {
      return;
    }
    const bounds = anchor.getBoundingClientRect();
    setRect({ top: bounds.bottom + 4, left: bounds.left, width: bounds.width });
  }, [anchorRef]);

  React.useLayoutEffect(() => {
    if (!isOpen) {
      return;
    }
    updatePosition();

    window.addEventListener("scroll", updatePosition, true);
    window.addEventListener("resize", updatePosition);
    return () => {
      window.removeEventListener("scroll", updatePosition, true);
      window.removeEventListener("resize", updatePosition);
    };
  }, [isOpen, updatePosition]);

  if (!isOpen || !mounted || !rect) {
    return null;
  }

  return createPortal(
    <div
      style={{
        position: "fixed",
        top: rect.top,
        left: rect.left,
        width: rect.width,
      }}
      onMouseDown={(event) => {
        event.stopPropagation();
      }}
      className={cn(
        "z-50 max-h-64 overflow-auto rounded-lg border border-emerald-200 bg-white p-1 shadow-lg",
        className,
      )}
    >
      {children}
    </div>,
    document.body,
  );
}

function ComboboxEmpty({ className, children }: React.ComponentProps<"div">) {
  const { filteredItems } = useComboboxContext();
  if (filteredItems.length > 0) {
    return null;
  }

  return (
    <div className={cn("px-2 py-1.5 text-sm text-slate-500", className)}>
      {children}
    </div>
  );
}

type ComboboxListProps = {
  children: (item: string) => React.ReactNode;
};

function ComboboxList({ children }: ComboboxListProps) {
  const { filteredItems } = useComboboxContext();
  return <div>{filteredItems.map((item) => children(item))}</div>;
}

type ComboboxItemProps = {
  value: string;
  disabled?: boolean;
  className?: string;
  children: React.ReactNode;
};

function ComboboxItem({
  value,
  disabled,
  className,
  children,
}: ComboboxItemProps) {
  const { selectItem } = useComboboxContext();

  return (
    <button
      type="button"
      disabled={disabled}
      onMouseDown={(event) => {
        event.preventDefault();
        event.stopPropagation();
      }}
      onClick={() => selectItem(value)}
      className={cn(
        "flex w-full items-center rounded-md px-2 py-1.5 text-left text-sm text-slate-700 hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
    >
      {children}
    </button>
  );
}

export {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
};
