import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Text } from "@chakra-ui/react";
import { FiTrash2 } from "react-icons/fi";

import { CollectionsService, type CollectionPublic, type ApiError } from "@/client";
import useCustomToast from "@/hooks/useCustomToast";
import { handleError } from "@/utils";
import {
  DialogRoot,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
  DialogCloseTrigger,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface DeleteCollectionProps {
  collection: CollectionPublic;
}

const DeleteCollection = ({ collection }: DeleteCollectionProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const queryClient = useQueryClient();
  const { showSuccessToast } = useCustomToast();
  const {
    handleSubmit,
    formState: { isSubmitting },
  } = useForm();

  const mutation = useMutation({
    mutationFn: () => CollectionsService.deleteCollection({ id: collection.id }),
    onSuccess: () => {
      showSuccessToast("Collection deleted successfully.");
      queryClient.invalidateQueries({ queryKey: ["collections"] });
      setIsOpen(false);
    },
    onError: (err: ApiError) => {
      handleError(err);
      setIsOpen(false);
    },
  });

  const onSubmit = () => {
    mutation.mutate();
  };

  return (
    <DialogRoot
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
      size={{ base: "xs", md: "md" }}
    >
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" colorPalette="red">
          <FiTrash2 />
          Delete Collection
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Delete Collection</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text>
              Are you sure you want to delete the collection named{" "}
              <strong>{collection.name}</strong>? This action cannot be undone.
            </Text>
          </DialogBody>
          <DialogFooter gap={2}>
            <Button
              variant="subtle"
              onClick={() => setIsOpen(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              colorPalette="red"
              type="submit"
              loading={isSubmitting}
            >
              Delete
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  );
};

export default DeleteCollection;