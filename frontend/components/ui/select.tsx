import * as React from "react"

import {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
} from "@/components/ui/combobox"
import { cn } from "@/lib/utils"

type SelectProps = Omit<React.ComponentProps<"select">, "ref"> & {
  searchable?: boolean
  placeholder?: string
}

function Select({ className, children, searchable = true, onChange, value, defaultValue, multiple, ...props }: SelectProps) {
  const options = React.Children.toArray(children)
    .filter((child) => React.isValidElement(child) && child.type === "option")
    .map((child) => {
      const option = child as React.ReactElement<React.ComponentProps<"option">>
      const label = React.Children.toArray(option.props.children)
        .map((part) => (typeof part === "string" || typeof part === "number" ? String(part) : ""))
        .join("")
      return {
        value: String(option.props.value ?? ""),
        label,
        disabled: option.props.disabled ?? false,
      }
    })

  if (searchable && !multiple) {
    const inputProps = props as unknown as React.ComponentProps<"input">
    const currentRawValue = value === undefined || value === null ? "" : String(value)
    const initialRawValue = defaultValue === undefined || defaultValue === null ? "" : String(defaultValue)
    const optionByValue = new Map(options.map((option) => [option.value, option]))
    const currentValue = optionByValue.get(currentRawValue)?.label ?? currentRawValue
    const initialValue = optionByValue.get(initialRawValue)?.label ?? initialRawValue
    const items = options.map((option) => option.label)
    const optionByLabel = new Map(options.map((option) => [option.label, option]))

    return (
      <Combobox
        key={currentValue}
        items={items}
        value={currentValue}
        defaultValue={initialValue}
        onValueChange={(nextLabel) => {
          const mappedValue = optionByLabel.get(nextLabel)?.value ?? nextLabel
          const syntheticEvent = {
            target: { value: mappedValue },
            currentTarget: { value: mappedValue },
          } as unknown as React.ChangeEvent<HTMLSelectElement>
          onChange?.(syntheticEvent)
        }}
      >
        <ComboboxInput
          data-slot="select"
          className={cn(
            "h-8 w-full min-w-0 rounded-lg border border-slate-300 bg-linear-to-br from-slate-50 via-slate-100 to-emerald-100 px-2.5 py-1 text-base text-slate-800 shadow-sm shadow-slate-400/20 transition-all duration-200 outline-none placeholder:text-slate-500 hover:border-emerald-400 focus-visible:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-400/30 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-slate-200 disabled:opacity-50 aria-invalid:border-red-500 aria-invalid:ring-2 aria-invalid:ring-red-300 file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-sm file:font-medium md:text-sm",
            className
          )}
          placeholder={inputProps.placeholder ?? "Rechercher..."}
          disabled={inputProps.disabled}
        />
        <ComboboxContent>
          <ComboboxEmpty>Aucun élément trouvé.</ComboboxEmpty>
          <ComboboxList>
            {(itemLabel) => {
              const option = optionByLabel.get(itemLabel)
              return (
                <ComboboxItem key={`${option?.value ?? itemLabel}-${itemLabel}`} value={itemLabel} disabled={option?.disabled}>
                  {itemLabel}
                </ComboboxItem>
              )
            }}
          </ComboboxList>
        </ComboboxContent>
      </Combobox>
    )
  }

  return (
    <select
      data-slot="select"
      value={value}
      defaultValue={defaultValue}
      onChange={onChange}
      multiple={multiple}
      className={cn(
        "h-8 w-full min-w-0 rounded-lg border border-slate-300 bg-linear-to-br from-slate-50 via-slate-100 to-emerald-100 px-2.5 py-1 text-base text-slate-800 shadow-sm shadow-slate-400/20 transition-all duration-200 outline-none placeholder:text-slate-500 hover:border-emerald-400 focus-visible:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-400/30 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-slate-200 disabled:opacity-50 aria-invalid:border-red-500 aria-invalid:ring-2 aria-invalid:ring-red-300 file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-sm file:font-medium md:text-sm",
        className
      )}
      {...props}
    >
      {children}
    </select>
  )
}

export { Select }