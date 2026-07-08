import { useState } from 'react';
import { Entity, EntityAttribute } from '@/types/entity';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Trash2 } from 'lucide-react';

interface EditEntityDialogProps {
  entity: Entity | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (entity: Entity) => void;
  onDelete?: () => void;
}

export const EditEntityDialog = ({
  entity,
  open,
  onOpenChange,
  onSave,
  onDelete,
}: EditEntityDialogProps) => {
  const [editedEntity, setEditedEntity] = useState<Entity | null>(entity);

  const handleAttributeChange = (attrName: string, newValue: any) => {
    if (!editedEntity) return;
    
    setEditedEntity({
      ...editedEntity,
      attributes: editedEntity.attributes.map((attr) =>
        attr.name === attrName ? { ...attr, value: newValue } : attr
      ),
    });
  };

  const handleNameChange = (newName: string) => {
    if (!editedEntity) return;
    setEditedEntity({
      ...editedEntity,
      public_identifier: newName,
    });
  };

  const handleSave = () => {
    if (editedEntity) {
      onSave(editedEntity);
      onOpenChange(false);
    }
  };

  if (!editedEntity) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit {editedEntity.type.replace('_', ' ')}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div>
            <Label htmlFor="entity-name">Name</Label>
            <Input
              id="entity-name"
              value={editedEntity.public_identifier}
              onChange={(e) => handleNameChange(e.target.value)}
              className="mt-1"
            />
          </div>

          {editedEntity.attributes.map((attr) => (
            <div key={attr.name}>
              <Label htmlFor={attr.name} className="capitalize">
                {attr.name.replace('_', ' ')}
              </Label>
              {attr.widget === 'array' ? (
                <div className="text-sm text-muted-foreground mt-1">
                  Array editing - {(attr.value as any[]).length} items
                </div>
              ) : (
                <Input
                  id={attr.name}
                  type={attr.widget === 'currency' ? 'number' : 'text'}
                  value={attr.value}
                  onChange={(e) =>
                    handleAttributeChange(
                      attr.name,
                      attr.widget === 'currency'
                        ? parseFloat(e.target.value)
                        : e.target.value
                    )
                  }
                  className="mt-1"
                />
              )}
            </div>
          ))}
        </div>

        <DialogFooter className="flex justify-between">
          <div>
            {onDelete && (
              <Button variant="destructive" size="sm" onClick={onDelete}>
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave}>Save Changes</Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
