import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  ColumnDef,
  SortingState,
  ColumnFiltersState,
} from '@tanstack/react-table';
import { ArrowUpDown, ChevronUp, ChevronDown, Download, Search, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface DataGridProps {
  data: any[];
  columns: ColumnDef<any>[];
  sortable?: boolean;
  filterable?: boolean;
  pagination?: boolean;
  pageSize?: number;
  editable?: boolean;
  onChange?: (rowIndex: number, columnId: string, value: any) => void;
  exportable?: boolean;
}

export const DataGrid = ({
  data,
  columns,
  sortable = true,
  filterable = true,
  pagination = true,
  pageSize = 10,
  editable = false,
  onChange,
  exportable = true,
}: DataGridProps) => {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = useState('');
  const [editingCell, setEditingCell] = useState<{ row: number; col: string } | null>(null);

  // Create table instance
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: sortable ? getSortedRowModel() : undefined,
    getFilteredRowModel: filterable ? getFilteredRowModel() : undefined,
    getPaginationRowModel: pagination ? getPaginationRowModel() : undefined,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    initialState: {
      pagination: {
        pageSize,
      },
    },
  });

  // Export to CSV
  const exportToCSV = () => {
    const headers = table.getAllColumns().map(col => col.id).join(',');
    const rows = table.getFilteredRowModel().rows.map(row => 
      table.getAllColumns().map(col => {
        const value = row.getValue(col.id);
        // Escape commas and quotes
        const stringValue = String(value ?? '');
        return stringValue.includes(',') || stringValue.includes('"') 
          ? `"${stringValue.replace(/"/g, '""')}"` 
          : stringValue;
      }).join(',')
    );
    
    const csv = [headers, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `data_export_${Date.now()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Handle cell edit
  const handleCellEdit = (rowIndex: number, columnId: string, newValue: any) => {
    onChange?.(rowIndex, columnId, newValue);
    setEditingCell(null);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-border bg-card"
    >
      {/* Toolbar */}
      {(filterable || exportable) && (
        <div className="flex items-center justify-between gap-4 p-4 border-b border-border">
          {filterable && (
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search all columns..."
                value={globalFilter}
                onChange={(e) => setGlobalFilter(e.target.value)}
                className="pl-9"
              />
            </div>
          )}
          
          {exportable && (
            <Button
              variant="outline"
              size="sm"
              onClick={exportToCSV}
              className="gap-2"
            >
              <Download className="h-4 w-4" />
              Export CSV
            </Button>
          )}
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="sticky top-0 bg-secondary">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-muted-foreground"
                  >
                    {header.isPlaceholder ? null : (
                      <div
                        className={`flex items-center gap-2 ${
                          sortable && header.column.getCanSort() ? 'cursor-pointer select-none' : ''
                        }`}
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {sortable && header.column.getCanSort() && (
                          <span className="flex items-center">
                            {header.column.getIsSorted() === 'asc' ? (
                              <ChevronUp className="h-4 w-4" />
                            ) : header.column.getIsSorted() === 'desc' ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ArrowUpDown className="h-4 w-4 opacity-50" />
                            )}
                          </span>
                        )}
                      </div>
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row, rowIdx) => (
              <motion.tr
                key={row.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: rowIdx * 0.03 }}
                className="border-t border-border hover:bg-muted/50 transition-colors"
              >
                {row.getVisibleCells().map((cell) => {
                  const isEditing =
                    editingCell?.row === row.index && editingCell?.col === cell.column.id;

                  return (
                    <td
                      key={cell.id}
                      className="px-4 py-3 text-sm text-foreground"
                      onDoubleClick={() => {
                        if (editable) {
                          setEditingCell({ row: row.index, col: cell.column.id });
                        }
                      }}
                    >
                      {isEditing ? (
                        <Input
                          autoFocus
                          defaultValue={cell.getValue() as string}
                          onBlur={(e) => handleCellEdit(row.index, cell.column.id, e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              handleCellEdit(row.index, cell.column.id, e.currentTarget.value);
                            } else if (e.key === 'Escape') {
                              setEditingCell(null);
                            }
                          }}
                          className="h-8"
                        />
                      ) : (
                        flexRender(cell.column.columnDef.cell, cell.getContext())
                      )}
                    </td>
                  );
                })}
              </motion.tr>
            ))}
          </tbody>
        </table>

        {/* Empty state */}
        {table.getRowModel().rows.length === 0 && (
          <div className="py-12 text-center text-muted-foreground">
            No data available
          </div>
        )}
      </div>

      {/* Pagination */}
      {pagination && table.getPageCount() > 1 && (
        <div className="flex items-center justify-between gap-4 px-4 py-3 border-t border-border">
          <div className="text-sm text-muted-foreground">
            Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} to{' '}
            {Math.min(
              (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
              table.getFilteredRowModel().rows.length
            )}{' '}
            of {table.getFilteredRowModel().rows.length} results
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            
            <div className="text-sm font-medium">
              Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
            </div>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </motion.div>
  );
};
