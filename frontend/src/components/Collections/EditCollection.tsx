import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { type SubmitHandler, useForm } from "react-hook-form";
import { Input, Text, VStack } from "@chakra-ui/react";
import { FiEdit } from "react-icons/fi";

import {
  CollectionsService,
  type CollectionPublic,
  type CollectionUpdate,
  type ApiError,
} from "@/client";
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
import { Field } from "@/components/ui/field";
import { Button } from "@/components/ui/button";

interface EditCollectionProps {
  collection: CollectionPublic;
}

const EditCollection = ({ collection }: EditCollectionProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const queryClient = useQueryClient();
  const { showSuccessToast } = useCustomToast();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isValid },
  } = useForm<CollectionUpdate>({
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: collection,
  });

  const mutation = useMutation({
    mutationFn: (data: CollectionUpdate) =>
      CollectionsService.updateCollection({
        id: collection.id,
        requestBody: data,
      }),
    onSuccess: () => {
      showSuccessToast("Collection updated successfully.");
      queryClient.invalidateQueries({ queryKey: ["collections"] });
      setIsOpen(false);
    },
    onError: (err: ApiError) => {
      handleError(err);
    },
  });

  const onSubmit: SubmitHandler<CollectionUpdate> = (data) => {
    mutation.mutate(data);
  };

  return (
    <DialogRoot
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
      size={{ base: "xs", md: "md" }}
    >
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm">
          <FiEdit />
          Edit Collection
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Edit Collection</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Update the collection details below.</Text>
            <VStack gap={4}>
              <Field
                required
                label="Name"
                invalid={!!errors.name}
                errorText={errors.name?.message}
              >
                <Input id="name" {...register("name")} type="text" />
              </Field>
              <Field label="Branch">
                <Input id="branch" {...register("branch")} type="text" />
              </Field>
              <Field label="Department">
                <Input id="department" {...register("department")} type="text" />
              </Field>
              <Field label="School">
                <Input id="school" {...register("school")} type="text" />
              </Field>
            </VStack>
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
              variant="solid"
              type="submit"
              loading={isSubmitting}
              disabled={!isValid}
            >
              Save Changes
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  );
};

export default EditCollection;