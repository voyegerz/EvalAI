import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type SubmitHandler, useForm } from "react-hook-form";
import { useState } from "react";
import { Input, Text, VStack } from "@chakra-ui/react";

import { type CollectionCreate, CollectionsService} from "@/client";
import type { ApiError } from "@/client/core/ApiError";
import useCustomToast from "@/hooks/useCustomToast";
import { handleError } from "@/utils";
import { Button } from "../ui/button";
import {
  DialogRoot,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
  DialogCloseTrigger,
  DialogTrigger,
} from "../ui/dialog";
import { Field } from "../ui/field";

const AddCollection = () => {
  const [isOpen, setIsOpen] = useState(false);
  const queryClient = useQueryClient();
  const { showSuccessToast } = useCustomToast();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isValid },
  } = useForm<CollectionCreate>({
    mode: "onBlur",
    criteriaMode: "all",
  });

  const mutation = useMutation({
    mutationFn: (data: CollectionCreate) =>
      CollectionsService.createCollection({ requestBody: data }),
    onSuccess: () => {
      showSuccessToast("Collection created successfully.");
      queryClient.invalidateQueries({ queryKey: ["collections"] });
      reset();
      setIsOpen(false);
    },
    onError: (err: ApiError) => {
      handleError(err);
    },
  });

  const onSubmit: SubmitHandler<CollectionCreate> = (data) => {
    mutation.mutate(data);
  };

  return (
    <DialogRoot
      open={isOpen}
      onOpenChange={({ open }) => setIsOpen(open)}
      size={{ base: "xs", md: "md" }}
    >
      <DialogTrigger asChild>
        <Button>Add Collection</Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Add New Collection</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Text mb={4}>Fill in the details for the new collection.</Text>
            <VStack gap={4}>
              <Field
                required
                label="Name"
                invalid={!!errors.name}
                errorText={errors.name?.message}
              >
                <Input
                  id="name"
                  {...register("name", {
                    required: "Name is required.",
                  })}
                  type="text"
                />
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
              Save
            </Button>
          </DialogFooter>
        </form>
        <DialogCloseTrigger />
      </DialogContent>
    </DialogRoot>
  );
};

export default AddCollection;