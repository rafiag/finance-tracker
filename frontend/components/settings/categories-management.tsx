'use client';

import { useEffect, useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  fetchCategories,
  createCategory,
  updateCategory,
  deleteCategory,
  Category,
} from '@/lib/services';
import { Plus, Edit2, Trash2, Loader2, ChevronRight, ChevronDown } from 'lucide-react';

interface CategoryNode {
  category: string;
  type: string;
  subcategories: string[];
}

export function CategoriesManagement() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [modalType, setModalType] = useState<'category' | 'subcategory'>('category');
  const [isSaving, setIsSaving] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  // Form state
  const [formData, setFormData] = useState({
    category: '',
    subcategory: '',
    type: 'Expense',
    parentCategory: '',
  });

  // Track which item is being edited
  const [editingItem, setEditingItem] = useState<{
    category: string;
    subcategory: string;
    type: string;
  } | null>(null);

  useEffect(() => {
    loadCategories();
  }, []);

  async function loadCategories() {
    try {
      setIsLoading(true);
      const data = await fetchCategories();
      setCategories(data);
    } catch (error) {
      console.error('Error loading categories:', error);
      alert('Failed to load categories');
    } finally {
      setIsLoading(false);
    }
  }

  // Group categories hierarchically
  const categoryTree = useMemo(() => {
    const income: CategoryNode[] = [];
    const expense: CategoryNode[] = [];

    // Group by category
    const grouped = new Map<string, CategoryNode>();

    categories.forEach((cat) => {
      if (!grouped.has(cat.name)) {
        grouped.set(cat.name, {
          category: cat.name,
          type: cat.type,
          subcategories: [],
        });
      }

      cat.subcategories.forEach((sub) => {
        if (sub) {
          grouped.get(cat.name)!.subcategories.push(sub);
        }
      });
    });

    // Separate by type
    grouped.forEach((node) => {
      if (node.type === 'Income') {
        income.push(node);
      } else {
        expense.push(node);
      }
    });

    return { income, expense };
  }, [categories]);

  const toggleExpand = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const handleCreateCategory = (type: string) => {
    setModalMode('create');
    setModalType('category');
    setFormData({ category: '', subcategory: '', type, parentCategory: '' });
    setEditingItem(null);
    setIsModalOpen(true);
  };

  const handleCreateSubcategory = (parentCategory: string, type: string) => {
    setModalMode('create');
    setModalType('subcategory');
    setFormData({ category: '', subcategory: '', type, parentCategory });
    setEditingItem(null);
    setIsModalOpen(true);
  };

  const handleEditCategory = (category: string, type: string) => {
    setModalMode('edit');
    setModalType('category');
    setFormData({ category, subcategory: '', type, parentCategory: '' });
    setEditingItem({ category, subcategory: '', type });
    setIsModalOpen(true);
  };

  const handleEditSubcategory = (category: string, subcategory: string, type: string) => {
    setModalMode('edit');
    setModalType('subcategory');
    setFormData({ category: '', subcategory, type, parentCategory: category });
    setEditingItem({ category, subcategory, type });
    setIsModalOpen(true);
  };

  const handleDelete = async (category: string, subcategory: string = '') => {
    const itemName = subcategory ? `subcategory "${subcategory}"` : `category "${category}"`;
    const confirmed = window.confirm(
      `Are you sure you want to delete ${itemName}?\n\n` +
        `All transactions using this ${subcategory ? 'subcategory' : 'category'} will be reassigned to "Uncategorized".`
    );

    if (!confirmed) return;

    try {
      await deleteCategory(category, subcategory);
      alert(`${itemName} deleted successfully`);
      loadCategories();
    } catch (error) {
      console.error('Error deleting category:', error);
      alert(`Failed to delete ${itemName}`);
    }
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);

      if (modalMode === 'create') {
        if (modalType === 'category') {
          await createCategory({
            category: formData.category,
            type: formData.type,
            subcategory: '',
          });
          alert(`Category "${formData.category}" created successfully`);
        } else {
          await createCategory({
            category: formData.parentCategory,
            type: formData.type,
            subcategory: formData.subcategory,
          });
          alert(`Subcategory "${formData.subcategory}" created successfully`);
        }
      } else {
        // Edit mode
        if (modalType === 'category') {
          await updateCategory(editingItem!.category, '', {
            new_category: formData.category,
          });
          alert('Category updated successfully');
        } else {
          await updateCategory(editingItem!.category, editingItem!.subcategory, {
            new_subcategory: formData.subcategory,
          });
          alert('Subcategory updated successfully');
        }
      }

      setIsModalOpen(false);
      loadCategories();
    } catch (error: any) {
      console.error('Error saving category:', error);
      alert(error?.message || 'Failed to save category');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return <div className="p-8 text-center">Loading categories...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Income Categories */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Income Categories</h3>
          <Button size="sm" onClick={() => handleCreateCategory('Income')} className="gap-2">
            <Plus className="h-4 w-4" />
            Add Category
          </Button>
        </div>

        <div className="rounded-md border bg-card">
          {categoryTree.income.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No income categories yet. Create one to get started.
            </div>
          ) : (
            <div className="divide-y">
              {categoryTree.income.map((node) => (
                <div key={node.category} className="p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={() => toggleExpand(node.category)}
                      >
                        {expandedCategories.has(node.category) ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </Button>
                      <span className="font-medium">{node.category}</span>
                      {node.subcategories.length > 0 && (
                        <span className="text-xs text-muted-foreground">
                          ({node.subcategories.length} subcategories)
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCreateSubcategory(node.category, 'Income')}
                      >
                        <Plus className="h-4 w-4 mr-1" />
                        Add Subcategory
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleEditCategory(node.category, 'Income')}
                      >
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(node.category)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </div>

                  {expandedCategories.has(node.category) && node.subcategories.length > 0 && (
                    <div className="ml-8 mt-2 space-y-1">
                      {node.subcategories.map((sub) => (
                        <div
                          key={sub}
                          className="flex items-center justify-between p-2 rounded hover:bg-muted"
                        >
                          <span className="text-sm">{sub}</span>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleEditSubcategory(node.category, sub, 'Income')}
                            >
                              <Edit2 className="h-3 w-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleDelete(node.category, sub)}
                            >
                              <Trash2 className="h-3 w-3 text-red-500" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Expense Categories */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Expense Categories</h3>
          <Button size="sm" onClick={() => handleCreateCategory('Expense')} className="gap-2">
            <Plus className="h-4 w-4" />
            Add Category
          </Button>
        </div>

        <div className="rounded-md border bg-card">
          {categoryTree.expense.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No expense categories yet. Create one to get started.
            </div>
          ) : (
            <div className="divide-y">
              {categoryTree.expense.map((node) => (
                <div key={node.category} className="p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6"
                        onClick={() => toggleExpand(node.category)}
                      >
                        {expandedCategories.has(node.category) ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </Button>
                      <span className="font-medium">{node.category}</span>
                      {node.subcategories.length > 0 && (
                        <span className="text-xs text-muted-foreground">
                          ({node.subcategories.length} subcategories)
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleCreateSubcategory(node.category, 'Expense')}
                      >
                        <Plus className="h-4 w-4 mr-1" />
                        Add Subcategory
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleEditCategory(node.category, 'Expense')}
                      >
                        <Edit2 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(node.category)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </div>

                  {expandedCategories.has(node.category) && node.subcategories.length > 0 && (
                    <div className="ml-8 mt-2 space-y-1">
                      {node.subcategories.map((sub) => (
                        <div
                          key={sub}
                          className="flex items-center justify-between p-2 rounded hover:bg-muted"
                        >
                          <span className="text-sm">{sub}</span>
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleEditSubcategory(node.category, sub, 'Expense')}
                            >
                              <Edit2 className="h-3 w-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleDelete(node.category, sub)}
                            >
                              <Trash2 className="h-3 w-3 text-red-500" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add/Edit Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {modalMode === 'create' ? 'Create' : 'Edit'}{' '}
              {modalType === 'category' ? 'Category' : 'Subcategory'}
            </DialogTitle>
            <DialogDescription>
              {modalMode === 'create'
                ? `Add a new ${modalType === 'category' ? 'category' : 'subcategory'} to organize your transactions.`
                : `Update the ${modalType === 'category' ? 'category' : 'subcategory'} name.`}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {modalType === 'subcategory' && modalMode === 'create' && (
              <div className="grid gap-2">
                <Label>Parent Category</Label>
                <Input value={formData.parentCategory} disabled />
              </div>
            )}

            <div className="grid gap-2">
              <Label htmlFor="name">
                {modalType === 'category' ? 'Category' : 'Subcategory'} Name *
              </Label>
              <Input
                id="name"
                value={modalType === 'category' ? formData.category : formData.subcategory}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    [modalType === 'category' ? 'category' : 'subcategory']: e.target.value,
                  })
                }
                placeholder={`e.g., ${
                  modalType === 'category' ? 'Salary, Food, Transport' : 'Restaurant, Grocery'
                }`}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsModalOpen(false)} disabled={isSaving}>
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={
                isSaving ||
                (modalType === 'category' && !formData.category) ||
                (modalType === 'subcategory' && !formData.subcategory)
              }
            >
              {isSaving ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : modalMode === 'create' ? (
                'Create'
              ) : (
                'Save Changes'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
