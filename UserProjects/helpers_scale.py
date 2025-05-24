import coat


def scale_selected_element(el: coat.SceneElement, scale_factor: float):
    el.selectOne()

    # Get the current 4x4 transformation matrix
    transform: coat.mat4 = el.getTransform()

    existing_scale: coat.vec3 = transform.GetScaling()
    new_scale = existing_scale * scale_factor
    transform.SetScaling(new_scale)
    el.setTransform(transform)
